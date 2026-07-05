// =============================================================================
// Jenkinsfile – MaxWeather API CI/CD Pipeline
// =============================================================================
// Stages:
//   1. Checkout   – clone the repo
//   2. Test       – build the Docker 'test' stage (runs pytest inside Docker)
//   3. Build      – build the final image + push to ACR using 'az acr build'
//   4. Deploy     – apply K8s manifests + rolling image update on AKS
//
// Requirements (configured in Jenkins before first run):
//   • Jenkins runs as a pod in AKS with managed identity (Phase 6)
//   • The AKS kubelet identity must have AcrPush on crmaxweathersea
//     (add via: az role assignment create --role AcrPush ...)
//   • Secret 'weather-api-secret' must already exist in the 'maxweather' namespace
//     (kubectl create secret generic weather-api-secret
//        --from-literal=OPENWEATHER_API_KEY=<key> -n maxweather)
// =============================================================================

pipeline {
    agent {
        kubernetes {
            label "maxweather-build-${BUILD_NUMBER}"
            defaultContainer "azure-cli"
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-agent
spec:
  nodeSelector:
    nodepool-type: user
  containers:
    - name: azure-cli
      image: mcr.microsoft.com/azure-cli:latest
      command: ["cat"]
      tty: true
      resources:
        requests:
          cpu: "300m"
          memory: "512Mi"
        limits:
          cpu: "1000m"
          memory: "1Gi"
"""
        }
    }

    environment {
        ACR_NAME        = "crmaxweathersea"
        ACR_URL         = "${ACR_NAME}.azurecr.io"
        IMAGE_REPO      = "maxweather/weather-api"
        IMAGE_TAG       = "${BUILD_NUMBER}"
        IMAGE_FULL      = "${ACR_URL}/${IMAGE_REPO}:${BUILD_NUMBER}"
        IMAGE_LATEST    = "${ACR_URL}/${IMAGE_REPO}:latest"
        K8S_NAMESPACE   = "maxweather"
        AKS_RG          = "rg-maxweather-demo-sea"
        AKS_NAME        = "aks-maxweather-demo-sea"
        APP_DIR         = "maxweather-app"
    }

    options {
        timeout(time: 30, unit: "MINUTES")
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: "10"))
    }

    stages {
        // ------------------------------------------------------------------
        stage("Checkout") {
        // ------------------------------------------------------------------
            steps {
                container("azure-cli") {
                    sh "apk add --no-cache git -q 2>/dev/null || true"
                }
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    echo "Building commit: ${env.GIT_COMMIT_SHORT}"
                }
            }
        }

        // ------------------------------------------------------------------
        stage("Test") {
        // ------------------------------------------------------------------
        // Builds the Docker 'test' stage — pytest runs INSIDE Docker.
        // The build fails here if any test fails (no test = no push).
        // ------------------------------------------------------------------
            steps {
                container("azure-cli") {
                    dir(APP_DIR) {
                        sh """
                            echo "=== Running tests via Docker test stage ==="
                            az login --identity
                            az acr build \\
                              --registry ${ACR_NAME} \\
                              --image ${IMAGE_REPO}-test:${IMAGE_TAG} \\
                              --target test \\
                              --file Dockerfile \\
                              .
                            echo "=== Tests passed ==="
                        """
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        stage("Build & Push") {
        // ------------------------------------------------------------------
        // Uses 'az acr build' – builds in the cloud, no Docker daemon needed.
        // Tags with both BUILD_NUMBER (immutable) and :latest.
        // ------------------------------------------------------------------
            steps {
                container("azure-cli") {
                    dir(APP_DIR) {
                        sh """
                            echo "=== Building and pushing final image ==="
                            az acr build \\
                              --registry ${ACR_NAME} \\
                              --image ${IMAGE_REPO}:${IMAGE_TAG} \\
                              --image ${IMAGE_REPO}:latest \\
                              --target final \\
                              --file Dockerfile \\
                              .
                            echo "=== Image pushed: ${IMAGE_FULL} ==="
                        """
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        stage("Deploy") {
        // ------------------------------------------------------------------
        // 1. Fetch AKS credentials (admin kubeconfig) via managed identity
        // 2. Apply all K8s manifests (namespace, configmap, deployment, service, hpa)
        // 3. Update the running image to the new build tag
        // 4. Wait for rollout to complete (timeout = 5 min)
        // ------------------------------------------------------------------
            steps {
                container("azure-cli") {
                    sh """
                        az login --identity
                        az aks get-credentials \\
                          --resource-group ${AKS_RG} \\
                          --name ${AKS_NAME} \\
                          --admin \\
                          --overwrite-existing
                    """
                    dir(APP_DIR) {
                        sh """
                            echo "=== Applying K8s manifests ==="
                            kubectl apply -f k8s/namespace.yaml
                            kubectl apply -f k8s/configmap.yaml
                            kubectl apply -f k8s/deployment.yaml
                            kubectl apply -f k8s/service.yaml
                            kubectl apply -f k8s/hpa.yaml

                            echo "=== Rolling update to image tag ${IMAGE_TAG} ==="
                            kubectl set image deployment/weather-api \\
                              weather-api=${IMAGE_FULL} \\
                              --namespace ${K8S_NAMESPACE}

                            echo "=== Waiting for rollout ==="
                            kubectl rollout status deployment/weather-api \\
                              --namespace ${K8S_NAMESPACE} \\
                              --timeout=300s

                            echo "=== Service endpoint ==="
                            kubectl get svc weather-api -n ${K8S_NAMESPACE}
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo """
╔══════════════════════════════════════════════╗
║  ✅  Deploy successful                        ║
║  Image : ${IMAGE_FULL}
║  Commit: ${env.GIT_COMMIT_SHORT ?: 'n/a'}
╚══════════════════════════════════════════════╝
            """
        }
        failure {
            echo "❌ Pipeline failed at stage: ${env.STAGE_NAME}. Check logs above."
        }
        always {
            deleteDir()
        }
    }
}

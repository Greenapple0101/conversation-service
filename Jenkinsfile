pipeline {
    agent any

    environment {
        DOCKERHUB = credentials('dockerhub-credentials')

        SONAR_TOKEN = credentials('sonar-token')
        SONAR_ORG   = credentials('SONAR_ORG')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')

        DOCKER_IMAGE = "yorange50/conversation"

        DEPLOY_USER = "ubuntu"
        DEPLOY_SERVER = "3.34.155.126"
        DEPLOY_PATH = "/home/ubuntu/k3s-deploy"
        YAML_FILE = "k3s-app.yaml"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "📦 GitHub에서 소스코드 가져오기"
                checkout scm
            }
        }

        /* ✅ Sonar는 develop / main / PR 에서만 */
        stage('SonarCloud Analysis') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH?.contains('develop') }
                    expression { env.GIT_BRANCH?.contains('main') }
                    changeRequest()
                }
            }
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'
                    sh """
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.organization=${SONAR_ORG} \
                          -Dsonar.host.url=https://sonarcloud.io \
                          -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('Quality Gate') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH?.contains('develop') }
                    expression { env.GIT_BRANCH?.contains('main') }
                    changeRequest()
                }
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        /* ✅ Docker Build: develop & main */
        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH?.contains('develop') }
                    expression { env.GIT_BRANCH?.contains('main') }
                }
            }
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:latest ."
            }
        }

        /* ✅ Docker Push: develop & main */
        stage('Login & Push Docker Image') {
            when {
                anyOf {
                    expression { env.GIT_BRANCH?.contains('develop') }
                    expression { env.GIT_BRANCH?.contains('main') }
                }
            }
            steps {
                sh """
                    echo ${DOCKERHUB_PSW} | docker login -u ${DOCKERHUB_USR} --password-stdin
                    docker push ${DOCKER_IMAGE}:latest
                """
            }
        }

        /* ✅ ✅ ✅ 운영 배포는 main에서만 */
        stage('Deploy to k3s Cluster') {
            when {
                expression { env.GIT_BRANCH?.contains('main') }
            }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                            kubectl set image deployment/conversation \
                              conversation-container=${DOCKER_IMAGE}:latest \
                            || kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 CI 성공 (운영 배포는 main일 때만 실행됨)"
        }
        failure {
            echo "❌ 품질 게이트 또는 빌드 실패"
        }
    }
}

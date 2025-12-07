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

        stage('SonarCloud Analysis') {
            when {
                branch 'develop'
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

        stage('Build Docker Image') {
            steps {
                echo "🐳 도커 이미지 빌드 중..."
                sh "docker build -t ${DOCKER_IMAGE}:latest ."
            }
        }

        stage('Login & Push Docker Image') {
            steps {
                sh """
                    echo ${DOCKERHUB_PSW} | docker login -u ${DOCKERHUB_USR} --password-stdin
                    docker push ${DOCKER_IMAGE}:latest
                """
            }
        }

        stage('Sync YAML to Server') {
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                            mkdir -p ${DEPLOY_PATH}
                        '
                        scp -o StrictHostKeyChecking=no ${YAML_FILE} \
                          ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/${YAML_FILE}
                    """
                }
            }
        }

        stage('Deploy to k3s Cluster') {
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                            kubectl set image deployment/conversation \
                              conversation-container=${DOCKER_IMAGE}:latest --record \
                            || kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 CI/CD + Sonar + 배포 성공!"
        }
        failure {
            echo "❌ 실패 - Jenkins 로그 확인"
        }
    }
}
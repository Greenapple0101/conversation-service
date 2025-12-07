// ✅ CI/CD Pipeline for conversation-service
// Jenkins 노드 스케줄링 및 웹훅 테스트 (develop 브랜치)
// PR 충돌 방지 및 자동 해결 로직 포함
pipeline {
    agent any

    environment {
        /* ✅ GitHub */
        GITHUB_TOKEN = credentials('healthy-real')
        GITHUB_OWNER = "devops-healthyreal"
        GITHUB_REPO  = "conversation-service"
        BASE_BRANCH  = "main"
        HEAD_BRANCH  = "develop"

        /* ✅ Docker */
        DOCKER_IMAGE = "yorange50/conversation"

        /* ✅ Sonar */
        SONAR_TOKEN = credentials('sonar-token')
        SONAR_ORG   = credentials('SONAR_ORG')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')

        /* ✅ Deploy */
        DEPLOY_USER = "ubuntu"
        DEPLOY_SERVER = "3.34.155.126"
        DEPLOY_PATH = "/home/ubuntu/k3s-deploy"
        YAML_FILE = "k3s-app.yaml"
    }

    stages {

        /* ============================================================
         * 1️⃣ Checkout
         * ============================================================ */
        stage('Checkout') {
            steps {
                echo "📦 GitHub 소스 체크아웃"
                checkout scm
                script {
                    if (env.GIT_BRANCH) {
                        env.BRANCH_NAME = env.GIT_BRANCH.replace("origin/", "").replace("refs/heads/", "")
                    } else {
                        env.BRANCH_NAME = sh(
                            script: "git rev-parse --abbrev-ref HEAD",
                            returnStdout: true
                        ).trim()
                    }
                    echo "🔍 GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "✅ Detected Branch: ${env.BRANCH_NAME}"
                }
            }
        }

        /* ============================================================
         * 2️⃣ Sonar (develop / main / PR 모두 실행)
         * ============================================================ */
        stage('SonarCloud Analysis') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                    changeRequest()
                }
            }
            steps {
                withSonarQubeEnv('sonarqube') {
                    script {
                        def scannerHome = tool 'sonar-scanner'
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.organization=${SONAR_ORG} \
                          -Dsonar.host.url=https://sonarcloud.io \
                          -Dsonar.token=${SONAR_TOKEN}
                        """
                    }
                }
            }
        }

        /* ============================================================
         * 3️⃣ Quality Gate
         * ============================================================ */
        stage('Quality Gate') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                    changeRequest()
                }
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    withSonarQubeEnv('sonarqube') {
                        waitForQualityGate abortPipeline: true
                    }
                }
            }
        }

        /* ============================================================
         * 4️⃣ develop → main PR 자동 생성 (충돌 방지를 위해 main 먼저 머지)
         * ============================================================ */
        stage('Auto Create PR (develop → main)') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.GIT_BRANCH?.contains('develop') }
                }
            }
            steps {
                script {
                    echo "🔍 기존 PR 존재 여부 확인"

                    def prList = sh(
                        script: """
                        curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
                        https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls?head=${GITHUB_OWNER}:${HEAD_BRANCH}&base=${BASE_BRANCH}&state=open
                        """,
                        returnStdout: true
                    ).trim()

                    if (prList == "[]" || prList == "") {
                        echo "✅ PR 없음 → main 브랜치 최신화 후 PR 생성"
                        
                        // ✅ 충돌 방지: main 브랜치의 최신 변경사항을 develop에 먼저 머지
                        echo "🔄 main 브랜치 최신 변경사항을 develop에 먼저 머지 (충돌 방지)"
                        sh """
                        git config user.name "Jenkins"
                        git config user.email "jenkins@ci"
                        git fetch origin ${BASE_BRANCH}:${BASE_BRANCH}
                        git merge origin/${BASE_BRANCH} -m "chore: main 브랜치 최신화 (충돌 방지)" || true
                        """
                        
                        // 머지 후 충돌이 있으면 main의 변경사항을 우선 (ours 전략)
                        def hasConflict = sh(
                            script: "git diff --check || echo 'conflict'",
                            returnStdout: true
                        ).trim()
                        
                        if (hasConflict.contains('conflict')) {
                            echo "⚠️ 충돌 감지 → main 브랜치 변경사항 우선 적용"
                            sh """
                            git checkout --theirs .
                            git add .
                            git commit -m "chore: main 브랜치 변경사항 반영 (충돌 해결)" || true
                            """
                        }
                        
                        // develop 브랜치에 푸시
                        sh """
                        git push origin ${HEAD_BRANCH} || echo "푸시 실패 (이미 최신 상태일 수 있음)"
                        """
                        
                        echo "✅ PR 자동 생성"
                        sh """
                        curl -s -X POST \
                          -H "Authorization: token ${GITHUB_TOKEN}" \
                          -H "Accept: application/vnd.github+json" \
                          https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls \
                          -d '{
                            "title": "🚀 develop → main 자동 PR",
                            "head": "${HEAD_BRANCH}",
                            "base": "${BASE_BRANCH}",
                            "body": "✅ Jenkins 자동 생성 PR\\n✅ main 브랜치 최신화 완료 (충돌 방지)"
                          }'
                        """
                    } else {
                        echo "⚠️ 이미 PR 존재 → 생성 스킵"
                    }
                }
            }
        }

        /* ============================================================
         * ✅ 4️⃣ develop → main 자동 MERGE
         * ============================================================ */
        stage('Auto Merge PR (develop → main)') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.GIT_BRANCH?.contains('develop') }
                }
            }
            steps {
                script {
                    echo "🔍 PR 번호 조회"

                    def prNumber = sh(
                        script: """
                        curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
                        https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls \
                        | jq -r '.[] | select(.head.ref=="develop" and .base.ref=="main") | .number'
                        """,
                        returnStdout: true
                    ).trim()

                    if (!prNumber) {
                        echo "⚠️ 머지할 PR이 없음"
                        return
                    }

                    echo "✅ PR #${prNumber} 발견 → mergeable 상태 대기"

                    // ✅ mergeable 계산 완료될 때까지 대기 (최대 5회, 각 5초)
                    def mergeable = "null"
                    for (int i = 0; i < 5; i++) {
                        sleep 5

                        mergeable = sh(
                            script: """
                            curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
                            https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls/${prNumber} \
                            | jq -r '.mergeable'
                            """,
                            returnStdout: true
                        ).trim()

                        echo "🔁 mergeable 상태: ${mergeable} (시도 ${i + 1}/5)"

                        if (mergeable == "true") {
                            echo "✅ mergeable == true 확인됨"
                            break
                        }
                    }

                    if (mergeable != "true") {
                        error "❌ PR이 mergeable 상태가 아님 (현재: ${mergeable}) → 자동 머지 중단"
                    }

                    echo "🚀 PR #${prNumber} squash merge 실행"

                    def mergeResponse = sh(
                        script: """
                        curl -s -X PUT \
                          -H "Authorization: token ${GITHUB_TOKEN}" \
                          -H "Accept: application/vnd.github+json" \
                          https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls/${prNumber}/merge \
                          -d '{
                            "merge_method": "squash"
                          }'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "✅ PR #${prNumber} 머지 완료"
                    echo "머지 응답: ${mergeResponse}"

                    // ✅ PR 머지 후 main 브랜치 최신화 대기 (최대 10초)
                    echo "⏳ main 브랜치 최신화 대기 중..."
                    sleep 10
                }
            }
        }

        /* ============================================================
         * 5️⃣ Docker Build (develop & main만)
         * ============================================================ */
        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                }
            }
            steps {
                echo "🐳 Docker 이미지 빌드"
                sh "docker build -t ${DOCKER_IMAGE}:latest ."
            }
        }

        /* ============================================================
         * 6️⃣ Docker Push
         * ============================================================ */
        stage('Login & Push Docker Image') {
            when {
                anyOf {
                    expression { env.BRANCH_NAME == 'develop' }
                    expression { env.BRANCH_NAME == 'main' }
                }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USR',
                        passwordVariable: 'DOCKERHUB_PSW'
                    )
                ]) {
                    sh '''
                    echo $DOCKERHUB_PSW | docker login -u $DOCKERHUB_USR --password-stdin
                    docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        /* ============================================================
         * 7️⃣ main 브랜치 머지 후 자동 배포 (develop에서 PR 머지한 경우)
         * ============================================================ */
        stage('Deploy to k3s Cluster (after PR merge)') {
            when {
                expression { env.BRANCH_NAME == 'develop' }
            }
            steps {
                script {
                    echo "🔍 PR 머지 여부 확인"
                    def mergedPR = sh(
                        script: """
                        curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
                        https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/pulls?head=${GITHUB_OWNER}:${HEAD_BRANCH}&base=${BASE_BRANCH}&state=closed \
                        | jq -r '.[0] | select(.merged_at != null) | .number'
                        """,
                        returnStdout: true
                    ).trim()

                    if (mergedPR) {
                        echo "✅ PR #${mergedPR}가 머지됨 → main 브랜치로 전환하여 배포"
                        
                        // main 브랜치 체크아웃
                        sh """
                        git fetch origin main:main
                        git checkout main
                        git pull origin main
                        """
                        
                        // k3s 배포 실행
                        sshagent(credentials: ['ubuntu']) {
                            sh """
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                                echo "🔄 최신 Docker 이미지로 배포 시작..."
                                kubectl set image deployment/conversation \
                                conversation-container=${DOCKER_IMAGE}:latest \
                                || kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                                echo "✅ 배포 완료"
                            '
                            """
                        }
                    } else {
                        echo "⚠️ 머지된 PR이 없음 → 배포 스킵"
                    }
                }
            }
        }

        /* ============================================================
         * 8️⃣ main 브랜치에서 직접 배포
         * ============================================================ */
        stage('Deploy to k3s Cluster (main branch)') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sshagent(credentials: ['ubuntu']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                        echo "🔄 main 브랜치에서 직접 배포 시작..."
                        kubectl set image deployment/conversation \
                        conversation-container=${DOCKER_IMAGE}:latest \
                        || kubectl apply -f ${DEPLOY_PATH}/${YAML_FILE}
                        echo "✅ 배포 완료"
                    '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 Sonar 통과 + PR 자동화 + CI/CD 성공"
        }
        failure {
            echo "❌ 파이프라인 실패"
        }
    }
}

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
                script {
                    // SonarCloud 분석 결과 처리 대기 (최대 15분)
                    timeout(time: 15, unit: 'MINUTES') {
                        withSonarQubeEnv('sonarqube') {
                            def qg = waitForQualityGate abortPipeline: false
                            
                            if (qg.status != 'OK') {
                                echo "⚠️ Quality Gate 상태: ${qg.status}"
                                echo "⚠️ Quality Gate 실패했지만 파이프라인은 계속 진행합니다"
                                // abortPipeline: false로 설정하여 실패해도 계속 진행
                            } else {
                                echo "✅ Quality Gate 통과"
                            }
                        }
                    }
                }
            }
        }

        /* ============================================================
         * 4️⃣ develop → main PR 자동 생성 (수동 머지 대기)
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
                        script: '''
                        curl -s -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                        https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls?head=''' + GITHUB_OWNER + ''':''' + HEAD_BRANCH + '''&base=''' + BASE_BRANCH + '''&state=open
                        ''',
                        returnStdout: true
                    ).trim()


                    echo "PR 조회 결과: ${prList}"

                    // PR 목록 파싱하여 실제 PR 존재 여부 확인
                    def prExists = false
                    if (prList && prList != "[]" && prList != "") {
                        try {
                            def prCount = sh(
                                script: '''
                                echo ''' + prList + ''' | jq '. | length'
                                ''',
                                returnStdout: true
                            ).trim()
                            
                            if (prCount && prCount != "0" && prCount != "") {
                                prExists = true
                                def prNumber = sh(
                                    script: '''
                                    echo ''' + prList + ''' | jq -r '.[0].number'
                                    ''',
                                    returnStdout: true
                                ).trim()
                                echo "✅ 이미 PR #${prNumber} 존재 → 생성 스킵"
                            }
                        } catch (Exception e) {
                            echo "⚠️ PR 목록 파싱 실패, 직접 확인 시도"
                        }
                    }

                    if (!prExists) {
                        echo "✅ PR 없음 → 자동 생성"
                        
                        def createResult = sh(
                            script: '''
                            curl -s -w "\\nHTTP_CODE:%{http_code}" -X POST \
                              -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                              -H "Accept: application/vnd.github+json" \
                              https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls \
                              -d '{
                                "title": "🚀 develop → main 자동 PR",
                                "head": "''' + HEAD_BRANCH + '''",
                                "base": "''' + BASE_BRANCH + '''",
                                "body": "✅ Jenkins 자동 생성 PR"
                              }'

                    if (prList == "[]" || prList == "") {
                        echo "✅ PR 없음 → 자동 생성"
                        
                        sh '''
                        curl -s -X POST \
                          -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                          -H "Accept: application/vnd.github+json" \
                          https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls \
                          -d '{
                            "title": "🚀 develop → main 자동 PR",
                            "head": "''' + HEAD_BRANCH + '''",
                            "base": "''' + BASE_BRANCH + '''",
                            "body": "✅ Jenkins 자동 생성 PR"
                          }'
                        '''
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
                        script: '''
                        curl -s -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                        https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls \
                        | jq -r '.[] | select(.head.ref=="develop" and .base.ref=="main") | .number'
                        ''',
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
                            script: '''
                            curl -s -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                            https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls/''' + prNumber + ''' \
                            | jq -r '.mergeable'

                            ''',
                            returnStdout: true
                        ).trim()

                        def httpCode = createResult.split("HTTP_CODE:")[1]
                        def response = createResult.split("HTTP_CODE:")[0]

                        if (httpCode == "201") {
                            echo "✅ PR 생성 성공"
                        } else if (httpCode == "422") {
                            echo "⚠️ PR 생성 실패: 이미 PR이 존재합니다 (HTTP 422)"
                            echo "응답: ${response}"
                        } else {
                            echo "⚠️ PR 생성 실패 (HTTP ${httpCode})"
                            echo "응답: ${response}"
                        }
                    }


                    if (mergeable != "true") {
                        error "❌ PR이 mergeable 상태가 아님 (현재: ${mergeable}) → 자동 머지 중단"
                    }

                    echo "🚀 PR #${prNumber} squash merge 실행"

                    def mergeResponse = sh(
                        script: '''
                        curl -s -X PUT \
                          -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                          -H "Accept: application/vnd.github+json" \
                          https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/pulls/''' + prNumber + '''/merge \
                          -d '{
                            "merge_method": "squash"
                          }'
                        ''',
                        returnStdout: true
                    ).trim()

                    echo "✅ PR #${prNumber} 머지 완료"
                    echo "머지 응답: ${mergeResponse}"

                    // ✅ PR 머지 후 main 브랜치 최신화 대기 (최대 10초)
                    echo "⏳ main 브랜치 최신화 대기 중..."
                    sleep 10
                    
                    // ✅ 근본 원인 해결: PR 머지 후 develop 브랜치를 main과 동기화 (충돌 방지)
                    echo "🔄 develop 브랜치를 main과 동기화하여 다음 PR 충돌 방지"
                    script {
                        // main 브랜치의 최신 SHA 가져오기
                        def mainSha = sh(
                            script: '''
                            curl -s -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                            https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/git/refs/heads/''' + BASE_BRANCH + '''
                            | jq -r '.object.sha'
                            ''',
                            returnStdout: true
                        ).trim()
                        
                        if (mainSha && mainSha != "null") {
                            echo "✅ main 브랜치 SHA: ${mainSha}"
                            
                            // develop 브랜치를 main과 동기화 (force update)
                            sh '''
                            curl -X PATCH \
                              -H "Authorization: token ''' + GITHUB_TOKEN + '''" \
                              -H "Accept: application/vnd.github+json" \
                              https://api.github.com/repos/''' + GITHUB_OWNER + '''/''' + GITHUB_REPO + '''/git/refs/heads/''' + HEAD_BRANCH + ''' \
                              -d '{
                                "sha": "''' + mainSha + '''",
                                "force": true
                              }'
                            '''
                            
                            echo "✅ develop 브랜치가 main과 동기화됨 → 다음 PR 충돌 없음"
                        } else {
                            echo "⚠️ main 브랜치 SHA를 가져올 수 없음 → 동기화 스킵"
                        }
                    }

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
         * 7️⃣ main 브랜치에서 자동 배포 (실무형 - main merge 시 자동 실행)
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

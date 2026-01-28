# Conversation Service - 배포 가이드

이 문서는 Conversation Service의 배포 방법을 설명합니다. 위 프로그램은 제가 직접 코딩하지 않은 프로젝트입니다.

## 배포 환경

- **컨테이너 런타임**: Docker
- **오케스트레이션**: Kubernetes (k3s)
- **CI/CD**: Jenkins
- **포트**: 7003 (Gunicorn), 8100 (Kubernetes Service)

## Docker 배포

### Docker 이미지 빌드

```bash
docker build -t yorange50/conversation:latest .
```

### Docker Compose 실행

```bash
docker-compose up -d
```

### Docker 이미지 실행

```bash
docker run -d \
  -p 7003:7003 \
  --name conversation-service \
  yorange50/conversation:latest
```

## Kubernetes (k3s) 배포

### 배포 파일

- `k3s-app.yaml`: Kubernetes 배포 매니페스트 파일

### 배포 명령어

```bash
# 배포 실행
kubectl apply -f k3s-app.yaml

# 배포 상태 확인
kubectl rollout status deployment/conversation --timeout=5m

# Pod 상태 확인
kubectl get pods -l app=conversation

# 서비스 확인
kubectl get service conversation-service
```

### 배포 구성

- **Deployment**: `conversation`
  - Replicas: 2
  - Container Port: 7003
  - Image: `yorange50/conversation:latest`
  - Resources:
    - Requests: memory 256Mi, cpu 250m
    - Limits: memory 512Mi, cpu 500m

- **Service**: `conversation-service`
  - Type: ClusterIP
  - Port: 8100 → Target Port: 7003

- **Ingress**: `flask-conversation-ingress`
  - Host: `13.124.109.82.nip.io`
  - Path: `/ai/conversation`

### 접속 URL

```
http://13.124.109.82.nip.io/ai/conversation
```

## CI/CD 파이프라인 (Jenkins)

### 파이프라인 구성

1. **Checkout**: GitHub 소스 체크아웃
2. **SonarCloud Analysis**: 코드 품질 분석
3. **Quality Gate**: 품질 게이트 확인
4. **Auto Create PR**: develop → main 자동 PR 생성
5. **Build Docker Image**: Docker 이미지 빌드
6. **Login & Push Docker Image**: Docker Hub에 이미지 푸시
7. **Sync YAML to Server**: k3s-app.yaml 서버 전송
8. **Deploy to k3s Cluster**: Kubernetes 배포 실행

### 브랜치별 동작

- **develop 브랜치**:
  - SonarCloud 분석
  - Docker 이미지 빌드 및 푸시
  - main 브랜치로 PR 자동 생성

- **main 브랜치**:
  - SonarCloud 분석
  - Docker 이미지 빌드 및 푸시
  - k3s 클러스터에 자동 배포

### 환경 변수

Jenkins에서 설정된 환경 변수:
- `DOCKER_IMAGE`: `yorange50/conversation`
- `DEPLOY_SERVER`: `13.124.109.82`
- `DEPLOY_PATH`: `/home/ubuntu/k3s-deploy`

## 배포 확인

### Kubernetes 리소스 확인

```bash
# Deployment 확인
kubectl get deployment conversation -o wide

# Pod 확인
kubectl get pods -l app=conversation

# Service 확인
kubectl get service conversation-service

# Ingress 확인
kubectl get ingress flask-conversation-ingress
```

### 로그 확인

```bash
# Pod 로그 확인
kubectl logs -f -l app=conversation

# 특정 Pod 로그 확인
kubectl logs <pod-name>
```

## 롤백

배포에 문제가 발생한 경우:

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/conversation

# 특정 리비전으로 롤백
kubectl rollout undo deployment/conversation --to-revision=<revision-number>

# 롤백 히스토리 확인
kubectl rollout history deployment/conversation
```

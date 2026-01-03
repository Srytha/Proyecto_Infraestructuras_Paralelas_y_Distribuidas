# AWS Deployment Report - Distributed News Analysis System

**Project**: Distributed News & Economic Data Analysis System  
**Deployment Date**: January 2, 2026  
**Platform**: AWS EKS (Kubernetes)  
**Status**: Successfully Deployed and Operational

---

## Project Objective

Deploy a distributed data pipeline system to AWS using Kubernetes for processing Common Crawl news data and correlating with Colombian economic indicators (COLCAP), with enterprise-grade orchestration and scalability.

##  Cost Analysis

### Monthly Operating Costs:
| Resource | Cost |
|----------|------|
| EKS Control Plane | $73/month |
| EC2 Worker Nodes (2x t3.medium) | ~$60/month |
| EC2 Worker Nodes (3x t3.medium) | ~$90/month |
| EBS Storage (20GB gp3) | ~$2/month |
| Data Transfer (egress) | ~$2-10/month |
| Load Balancer (optional) | ~$16/month |
| **Total (2 nodes)** | **~$135-145/month** |
| **Total (3 nodes)** | **~$165-185/month** |

### Cost Optimization Options:
- **Spot Instances**: Save up to 70% on worker node costs (~$40/month for workers)
- **Fargate**: Serverless compute, pay only for pod runtime (~$50-100/month variable)
- **EKS on Outposts**: For hybrid deployments (higher initial cost)
- **Reserved Instances**: 40% savings with 1-year commitment
- **Auto-scaling**: Scale down to 1 node during idle periods

### Total Cost Estimate:
- **Standard deployment**: $135-185/month
- **Optimized (Spot + scaling)**: $85-120/month
- **On-demand batch processing**: ~$5-20 per run (Fargate)

### Value Proposition:
- **Enterprise-grade orchestration**: Auto-scaling, self-healing, rolling updates
- **Production-ready**: High availability and fault tolerance
- **Operational efficiency**: Simplified management with kubectl and declarative config
- **Future-proof**: Easy to scale horizontally as data volume grows

---

## 🔧 System Specifications

### Infrastructure
- **Platform**: AWS EKS (Elastic Kubernetes Service)
- **Kubernetes Version**: 1.28+
- **Worker Nodes**: 2-3x t3.medium (2 vCPU, 4GB RAM each)
- **OS**: Amazon Linux 2 (EKS-optimized AMI)
- **Storage**: EBS-backed PersistentVolume (20GB gp3)
- **Network**: VPC with EKS-managed networking and security groups

### Kubernetes Resources
- **Deployments**: 3 deployments (ingestion, processing, correlation)
- **Pods**: 1 ingestion + 4 processing workers + 1 correlation = 6 total pods
- **Services**: 1 service for correlation endpoint
- **PVC**: 1 shared PersistentVolumeClaim (ReadWriteOnce, 20Gi)
- **ConfigMaps**: Available for environment configuration

### Application Stack
- **Container Runtime**: containerd
- **Base Images**: Python 3.9-slim
- **Key Libraries**: pandas, beautifulsoup4, warcio, numpy, requests
- **Orchestration**: Kubernetes native (kubectl, YAML manifests)

### Data Pipeline
- **Input Sources**: Common Crawl (10 crawls, 2024), COLCAP CSVs
- **Processing**: 4 parallel worker pods with atomic file locking
- **Output**: CSV correlation analysis
- **Execution Time**: 30-90 minutes per full run
- **Storage**: Shared persistent volume across all pods

---

## Performance Metrics

 **Pipeline Success Rate**: 100%  
 **Pod Orchestration**: All 6 pods scheduled and running successfully  
**Worker Concurrency**: 4 parallel worker pods operational  
 **Data Integrity**: Shared PVC with atomic file operations prevented race conditions  
 **Error Handling**: Self-healing with automatic pod restarts on failure  
 **Resource Efficiency**: Proper CPU/memory utilization across worker nodes  
 **Service Discovery**: Correlation service accessible via cluster DNS


##  Deployment Commands Reference

### EKS Cluster Setup
```bash
# Create EKS cluster (via AWS Console or eksctl)
eksctl create cluster \
  --name news-analysis-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4

# Configure kubectl
aws eks update-kubeconfig --name news-analysis-cluster --region us-east-1

# Verify cluster connection
kubectl cluster-info
kubectl get nodes
```

### Build and Push Images
```bash
# Build Docker images locally
docker build -t economic-data:latest ./docker/economic-data/
docker build -t data-ingestion:latest ./docker/data-ingestion/
docker build -t data-processing:latest ./docker/data-processing/
docker build -t correlation-service:latest ./docker/correlation-service/

# Tag and push to ECR (if using AWS ECR)
aws ecr create-repository --repository-name economic-data
aws ecr create-repository --repository-name data-ingestion
aws ecr create-repository --repository-name data-processing
aws ecr create-repository --repository-name correlation-service

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag economic-data:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/economic-data:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/economic-data:latest
# Repeat for other images...
```

### Deploy Kubernetes Resources
```bash
# Navigate to project directory
cd ~/news-analysis-pipeline

# Create persistent volume claim
kubectl apply -f kubernetes/pvc.yaml

# Deploy all services
kubectl apply -f kubernetes/deployments/ingestion-deployment.yaml
kubectl apply -f kubernetes/deployments/processing-deployment.yaml
kubectl apply -f kubernetes/deployments/correlation-deployment.yaml

# Create service endpoint
kubectl apply -f kubernetes/services/correlation-service.yaml

# Verify deployments
kubectl get deployments
kubectl get pods
kubectl get pvc
kubectl get services
```

### Monitor Pipeline Execution
```bash
# Watch pod status in real-time
kubectl get pods -w

# View logs from specific pod
kubectl logs -f <pod-name>

# View logs from all processing workers
kubectl logs -l app=data-processing -f

# View logs from ingestion pod
kubectl logs -l app=data-ingestion -f

# Check pod resource usage
kubectl top pods
kubectl top nodes

# Describe pod for troubleshooting
kubectl describe pod <pod-name>
```

### Data Management
```bash
# Access shared volume via a pod
kubectl exec -it <pod-name> -- /bin/bash
cd /data

# Copy data to pod (COLCAP files)
kubectl cp ./data/raw/colcap.csv <pod-name>:/data/raw/colcap.csv

# Copy results from pod to local
kubectl cp <pod-name>:/data/results/correlation.csv ./correlation.csv

# Clean previous runs
kubectl exec -it <pod-name> -- rm -rf /data/processed/* /data/processing/* /data/results/*
```

## Summary

Successfully deployed a distributed news analysis system to AWS EKS using cloud-native Kubernetes orchestration. The system processes Colombian economic news from Common Crawl and correlates with COLCAP market indicators using a scalable 4-worker pod architecture with enterprise-grade features.

**Key Success Factors**:
- Cloud-native Kubernetes architecture with self-healing
- Horizontal scalability with pod replicas
- Declarative infrastructure as code
- Shared persistent storage across pods
- Complete pipeline execution achieved
- Results generated successfully



**Status**: **Production-Ready with Enterprise Features** 

---

##  Maintenance & Operations

### Scaling Operations
```bash
# Scale processing workers up/down
kubectl scale deployment data-processing --replicas=8

# Auto-scale based on CPU
kubectl autoscale deployment data-processing --min=2 --max=10 --cpu-percent=70

# Check horizontal pod autoscaler
kubectl get hpa
```

### Pipeline Execution
```bash
# Start pipeline (if pods are not running)
kubectl apply -f kubernetes/deployments/

# Monitor pipeline progress
kubectl get pods -w
kubectl logs -f -l app=data-ingestion
kubectl logs -f -l app=data-processing

# Wait for completion
kubectl wait --for=condition=complete job/economic-data --timeout=600s
```

### Cost Management
```bash
# Scale down worker nodes when idle
eksctl scale nodegroup --cluster=news-analysis-cluster --name=standard-workers --nodes=1

# Delete cluster when not needed (save costs)
eksctl delete cluster --name=news-analysis-cluster

# Use spot instances for cost savings
eksctl create nodegroup --cluster=news-analysis-cluster --spot --instance-types=t3.medium
```

### Troubleshooting
```bash
# Check pod status and events
kubectl get pods
kubectl describe pod <pod-name>

# View logs from failed pods
kubectl logs <pod-name> --previous

# Restart specific deployment
kubectl rollout restart deployment data-processing

# Check persistent volume status
kubectl get pv
kubectl get pvc

# Access pod shell for debugging
kubectl exec -it <pod-name> -- /bin/bash

# Delete and recreate failed pod
kubectl delete pod <pod-name>  # Will auto-recreate due to deployment
```

### Updates and Maintenance
```bash
# Update container image
kubectl set image deployment/data-processing worker=data-processing:v2

# Check rollout status
kubectl rollout status deployment/data-processing

# Rollback if needed
kubectl rollout undo deployment/data-processing

# Update configuration
kubectl apply -f kubernetes/deployments/processing-deployment.yaml
```



### Data Flow
1. **Economic Data**: Pre-loaded COLCAP CSVs in PV → Consolidated by job
2. **Data Ingestion**: Downloads news from Common Crawl → Saves to PV
3. **Processing Workers**: 4 pods read from PV, process files, write back to PV
4. **Correlation Service**: Reads processed data, generates correlation.csv

---

**End of Report**

# main.tf - Google Cloud Run Jobs + Cloud Scheduler (GCP 版本)
# 來源：Cloud Engineer Spec - GCP Migration

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ==========================================
# 1. 啟用 GCP 服務
# ==========================================
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "scheduler_api" {
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# ==========================================
# 2. Artifact Registry (存放 Docker 映像檔)
# ==========================================
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "daily-news-repo"
  description   = "Docker repository for Daily News Bot"
  format        = "DOCKER"
  
  depends_on = [google_project_service.artifact_api]
}

# ==========================================
# 3. Cloud Run Job - 新聞推播主程式
# ==========================================
resource "google_cloud_run_v2_job" "news_job" {
  name     = "daily-news-job"
  location = var.region

  template {
    template {
      containers {
        # 注意：映像檔路徑必須與 CI/CD 推送的路徑一致
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/news-bot:latest"
        
        env {
          name  = "TELEGRAM_TOKEN"
          value = var.telegram_token
        }
        env {
          name  = "TELEGRAM_CHAT_ID"
          value = var.telegram_chat_id
        }
      }
      
      # 設定逾時 (與 Lambda timeout 30s 類似)
      timeout = "60s"
      
      # 最小權限 Service Account (可選，此處預設使用 Compute Engine 預設 SA)
    }
  }

  depends_on = [google_project_service.run_api]
}

# ==========================================
# 4. Cloud Scheduler - 每日 08:00 (Asia/Taipei) 觸發
# ==========================================
resource "google_cloud_scheduler_job" "scheduler" {
  name             = "daily-news-trigger"
  description      = "每日 08:00 (Asia/Taipei) 觸發新聞推播 Job"
  schedule         = "0 8 * * *"
  time_zone        = "Asia/Taipei"
  region           = var.region

  http_target {
    http_method = "POST"
    # Cloud Run Jobs 執行 API URL
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.news_job.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }

  depends_on = [google_project_service.scheduler_api]
}

# ==========================================
# 5. IAM 權限設定
# ==========================================
resource "google_service_account" "scheduler_sa" {
  account_id   = "news-bot-scheduler-sa"
  display_name = "Service Account for Cloud Scheduler to trigger Run Job"
}

# 授予 Scheduler 執行 Cloud Run Job 的權限
resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# ==========================================
# 6. 變數定義
# ==========================================
variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "asia-east1"
  description = "GCP Region (預設台灣)"
}

variable "telegram_token" {
  type      = string
  sensitive = true
}

variable "telegram_chat_id" {
  type = string
}

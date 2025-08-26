## 1. Overview
- **Project Name**:  Divine Whispers
- **Goal / Background**:  
  > 在一些亞洲國家有所謂的廟宇求籤的信仰習俗，人在生活的過程會有各式各樣的煩惱，這時候可以去廟宇拜拜，詢問心中的煩惱透過抽出的詩籤不同可以解析一個未來可能的方向或建議，這些隨機的籤詩會包含好與不好的，主要是一個能夠為迷惘的人給予一些方向和提醒，即使是好的籤詩也要人們繼續努力運籌帷幄而即使是不好的籤詩也會讓人們調整好自己的心態在繼續面對，而我的這個應用核心概念與這個相同，主要提供的服務就是在解析一些我有提供的詩籤，使用者如果已經有求籤了，但通常仍需要解釋，而一般能找到的解釋都是很通用的，無法針對個人的狀況作出解析，我透過LLM以及一些解析的資訊提供個性化的解析，而另一方面我也提供沒有抽過籤的人進行抽籤後再進行解析以上兩種模式。

---

## 2. Functional Requirements
1. User Management
   - User registration
   - User login / logout
   - Authentication & authorization
   - Password reset / change

2. Data Management
   - CRUD for User account and history
   - Search / filter / sort
   - Pagination support

1. Workflow & Processing
   - Task scheduling / queue
   - Status tracking

4. Integration
   - Third-party API (e.g. payment)
   - Webhook support

5. Administration
   - Role-based access control
   - Activity logs / audit trail
   - System configuration

6. Monitoring & Health
   - Service health check endpoint
   - Metrics & logging

---

## 3. Non-Functional Requirements
- - **Performance**
    - API 一般請求回應時間 < 200ms（不含模型運算）
    - 模型運算屬於長時間任務，需即時回覆「已接收並處理中」的狀態（async pattern）
    - 支援 **任務狀態查詢 API**，讓前端（Web / App）可以輪詢或接收推播更新
- **Security**
    - **Authentication**：使用 JWT + Refresh Token，支援 Web（瀏覽器 Cookie / LocalStorage）與 App（Secure Storage）
    - **Authorization**：Role-based access control (RBAC)，確保管理員 / 使用者 / 金流 API 權限分明
    - **Data Security**：
        - 所有通訊必須走 HTTPS/TLS 1.2+
        - 使用者密碼加鹽雜湊（BCrypt / Argon2）
        - 金流交易資料（儲值、消費紀錄）需符合 **PCI DSS 基本安全規範**
    - **Abuse Protection**：Rate limiting + Captcha，防止惡意請求或金流濫用
- **Scalability**
    - 系統需支援水平擴展，API Gateway 能同時處理 Web 與 App 流量
    - 模型運算任務支援 **分散式排程**（e.g. 任務分派到不同 Worker/Pod）
    - 任務佇列（Message Queue，例如 Redis Stream / RabbitMQ / Kafka）支援高併發
- **Reliability**
    - 系統可用性 > 99.9%
    - 模型任務失敗需支援 **自動重試與錯誤回報**
    - 使用者支付流程必須具備 **交易一致性（例如透過 DB Transaction 或 Saga Pattern 保證「扣款成功 → 任務才成立」）**
    - 任務狀態持久化，避免因服務中斷而遺失
- **Usability**
    - Web 與 App 共用一致的 API 規格
    - 任務進度需可視化（例如：排隊中 → 執行中 → 完成 → 失敗），回傳標準化狀態碼
    - 支援多平台通知機制（WebSocket / Server-Sent Events / App Push Notification）
- **Maintainability**
    - API 版本化（/api/v1, /api/v2），確保 Web 與 App 不會因升級互相影響
    - Logging 與 Tracing：所有金流、模型任務需完整記錄可追溯
    - 支援自動化測試（Unit / Integration / Load Test）
---

## 4. Data Model

### 1. Users（使用者）

|Field|Type|Constraints|Description|
|---|---|---|---|
|user_id|BIGINT|PK, auto-increment|使用者唯一 ID|
|email|VARCHAR(255)|unique, not null|登入帳號|
|password_hash|VARCHAR(255)|not null|加鹽後 hash 密碼|
|role|VARCHAR(50)|default 'user'|user / admin / …|
|status|VARCHAR(20)|default 'active'|active / suspended / …|
|points_balance|INT|default 0|目前剩餘點數|
|created_at|TIMESTAMP|not null, default now()|註冊時間|
|updated_at|TIMESTAMP|not null, auto-update|更新時間|

---

### 2. Wallets（錢包／點數帳戶，1:1 對應 Users）

|Field|Type|Constraints|Description|
|---|---|---|---|
|wallet_id|BIGINT|PK, auto-increment|錢包唯一 ID|
|user_id|BIGINT|FK → Users.user_id|所屬使用者|
|balance|INT|default 0|當前點數餘額|
|updated_at|TIMESTAMP|auto-update|最後更新時間|

---

### 3. Transactions（金流／點數紀錄）

| Field        | Type         | Constraints                      | Description         |
| ------------ | ------------ | -------------------------------- | ------------------- |
| txn_id       | BIGINT       | PK, auto-increment               | 交易唯一 ID             |
| wallet_id    | BIGINT       | FK → Wallets.wallet_id           | 所屬錢包                |
| type         | ENUM         | [‘deposit’, ‘spend’, ‘refund’]   | 交易類型                |
| amount       | INT          | not null                         | 金額（正數 = 加點，負數 = 扣點） |
| reference_id | VARCHAR(255) | nullable                         | 金流平台或任務 ID          |
| status       | ENUM         | [‘pending’, ‘success’, ‘failed’] | 狀態                  |
| created_at   | TIMESTAMP    | not null, default now()          | 建立時間                |

> ✅ Wallets + Transactions 設計可以保留所有金流歷史，方便追蹤與稽核。

---

### 4. Jobs（任務請求）

|Field|Type|Constraints|Description|
|---|---|---|---|
|job_id|BIGINT|PK, auto-increment|任務唯一 ID|
|user_id|BIGINT|FK → Users.user_id|建立任務的使用者|
|txn_id|BIGINT|FK → Transactions.txn_id|扣點交易|
|status|ENUM|[‘pending’, ‘running’, ‘completed’, ‘failed’]|任務狀態|
|input_path|VARCHAR(500)|nullable|任務輸入資料（檔案路徑 / URL）|
|points_used|INT|not null|扣除點數數量|
|created_at|TIMESTAMP|not null, default now()|任務建立時間|
|updated_at|TIMESTAMP|auto-update|任務最後更新時間|
|expire_at|TIMESTAMP|nullable|任務結果保存期限|

---

### 5. JobResults（任務結果）

|Field|Type|Constraints|Description|
|---|---|---|---|
|result_id|BIGINT|PK, auto-increment|結果唯一 ID|
|job_id|BIGINT|FK → Jobs.job_id|對應任務|
|output_data|JSON / TEXT||模型輸出結果|
|file_path|VARCHAR(500)|nullable|存檔路徑或 URL|
|completed_at|TIMESTAMP|not null|完成時間|
|retention_until|TIMESTAMP|nullable|保留到期日（定期清理）|

---

### 6. AuditLogs（審計紀錄 / 安全追蹤）

|Field|Type|Constraints|Description|
|---|---|---|---|
|log_id|BIGINT|PK, auto-increment|Log 唯一 ID|
|user_id|BIGINT|FK → Users.user_id|誰觸發的操作|
|action|VARCHAR(255)|not null|動作（login / spend / …）|
|detail|TEXT|nullable|JSON / 補充細節|
|created_at|TIMESTAMP|not null, default now()|發生時間|

---

## 5. API Design
Please base on other requirement and consider how to using FortuneSystem and  try to design an elegant API design.

---

## 6. System Architecture

### 6.1 Overview
The system supports **Web and App clients**, provides **point-based model computation services**, and handles **financial transactions** securely. Built on **FastAPI** with **PostgreSQL**, it incorporates **event-driven mechanisms** for real-time task status and results delivery.

---
### 6.2 Components
1. **Backend API (FastAPI)**    
    - Handles user management, wallet/transaction logic, task submission, and audit logging        
2. **Database (PostgreSQL)**    
    - Stores persistent data: users, wallets, transactions, tasks, results, and audit logs        
3. **Event System**    
    - Manages task processing and completion events to decouple computation from API responses        
4. **Task / Model Service**    
    - Consumes task events, executes computations, writes results, and emits completion events        
5. **WebSocket / Client Notification**    
    - Maintains persistent connections to push task status and results to clients in real time
---

## 7. Deployment & Operations
### 7.1 Deployment
- **Containerization**: 使用 **Docker** 封裝後端 API、模型服務與依賴    
- **Hosting Options**: 可以部署在雲端虛擬主機（GCP Compute Engine 或 AWS EC2）    
- **Orchestration**: 個人開發階段可先直接用 Docker Compose 管理多容器    
    - 將 API、PostgreSQL放在同一 Compose        
- **Future Scalability**: 若後續需要可選用 **Kubernetes** 或 Cloud Run / ECS 進行容器編排
---
### 7.2 Environment
- **Dev**: 本地開發環境，使用 Docker Compose    
- **Staging**: 雲端 VM 測試環境，與 Production 配置相似    
- **Production**: 雲端 VM 部署 Docker 容器，暴露必要的 API 端口並配置 HTTPS
---
### 7.3 Monitoring
- 簡單監控可用 **Prometheus + Grafana**：    
    - 監控 API 服務狀態、容器資源（CPU、Memory）        
- 也可以搭配 **Cloud Provider Monitoring**（GCP Monitoring / AWS CloudWatch）    
- 個人開發階段可先只用 **Docker logs** + `docker stats`    
---
### 7.4 Logging
- **格式**: JSON 格式，便於後續分析與查詢    
- **內容**:    
    - Timestamp, Level, Module, Message, User ID / Job ID (必要)        
- **儲存方式**:
    - 本地文件 (`logs/` 目錄) 或雲端存儲（如 GCP Storage / AWS S3）        
- **輪替 / 保留**: 每日或每週產生新 log，舊 log 可自動壓縮或清理
---
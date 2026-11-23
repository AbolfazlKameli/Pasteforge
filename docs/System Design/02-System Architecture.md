## High Level Architecture
Incoming requests pass directly to the internal web server, which handles cross-cutting concerns such as rate limiting, HTTP caching, logging, metrics, compression, and load balancing. The application layer encapsulates the core business logic and services, keeping infrastructure concerns separate from application responsibilities.
A dedicated cache layer improves read performance, while the primary data store remains the **source of truth** for persistent data. This separation promotes clear responsibility boundaries, efficient data access, and a foundation for future scalability.
```mermaid
flowchart LR
    U["User"]

    subgraph IC["Internal Components"]
        LB["Load Balancer"]

        WS["Webserver<br/>Internal rate limiter<br/>HTTP Cache handling<br/>Logging<br/>Metrics<br/>Compression"]

        APP["Application/Services"]

        CACHE["Cache Layer"]

        DB["Source of truth"]

        LB --> WS
        WS --> APP
        APP --> CACHE
        CACHE --> DB
    end

    U --> LB

    style IC fill:#00000000,stroke:#35b66a,stroke-width:2px
    style U fill:#212529,stroke:#888,color:#ff6699
    style LB fill:#212529,stroke:#888,color:#ff6699
    style WS fill:#212529,stroke:#888,color:#ff6699
    style APP fill:#212529,stroke:#888,color:#ff6699
    style CACHE fill:#212529,stroke:#888,color:#ff6699
    style DB fill:#212529,stroke:#888,color:#ff6699
```

## Detailed Architecture
NGINX acts as the load balancer, distributing incoming traffic to the web server layer, where NGINX and Uvicorn handle request routing and infrastructure concerns such as internal rate limiting, HTTP caching, logging, metrics, and compression. The application layer is built with FastAPI and separates authentication, user management, and paste management into dedicated services.
Redis provides a cache layer using the **Cache-Aside Pattern**, reducing database reads for frequently accessed data, while PostgreSQL serves as the **source of truth** for persistent data. This design separates application responsibilities from infrastructure concerns and establishes clear boundaries between caching and durable storage.
```mermaid
flowchart LR
    U["User"]

    subgraph IC["Internal Components"]
        direction LR

        subgraph LB_GROUP[" "]
            direction TB
            LB["**Load Balancer**<br/><br/>NGINX"]
        end

        WS["**Webserver**<br/><br/>NGINX & Uvicorn<br/>Internal rate limiter<br/>HTTP Cache handling<br/>Logging<br/>Metrics<br/>Compression"]

        subgraph APP["Application/Services"]
            direction TB
            FAST["FastAPI"]
            AUTH["**Authentication Service**"]
            USERS["**User Management Service**"]
            PASTES["**Pastes Management Service**"]
        end

        CACHE["**Cache Layer**<br/><br/>Redis<br/>Cache-Aside Pattern"]

        DB["**Source of Truth**<br/><br/>PostgreSQL"]

        LB --> WS
        WS --> FAST
        APP --> CACHE
        CACHE <--> DB
    end

    U --> LB

    style IC fill:transparent,stroke:#777,stroke-width:1px
    style APP fill:transparent,stroke:#35b66a,stroke-width:2px
    style LB_GROUP fill:transparent,stroke:transparent

    classDef component fill:#212529,stroke:#888,color:#ff6699,stroke-width:1px
    classDef service fill:#212529,stroke:#888,color:#3185ff,stroke-width:1px
    classDef user fill:#212529,stroke:#888,color:#ff6699

    class U user
    class LB,WS,FAST component
    class AUTH,USERS,PASTES,CACHE,DB service
```
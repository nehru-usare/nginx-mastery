# NGINX Mastery: From Beginner to Production 🚀

A comprehensive, documentation-based learning system to achieve production-level mastery of NGINX, complete with hands-on projects and Docker Compose environments.

## 📖 Curriculum & Documentation
The theoretical knowledge is contained inside the `/docs` directory. Read through these sequentially to build your understanding:

1. **[Level 1: NGINX Fundamentals](docs/01-nginx-fundamentals.md)** - Architecture, event-driven model, configuration basics.
2. **[Level 2: Reverse Proxy & Load Balancing](docs/02-reverse-proxy-load-balancing.md)** - Upstreams, routing, header forwarding.
3. **[Level 3: SSL, HTTPS & Security](docs/03-ssl-https-security.md)** - TLS termination, Rate Limiting, CORS, Security headers.
4. **[Level 4: Performance & Caching](docs/04-performance-optimization.md)** - Gzip, proxy_cache, Keepalives, HTTP/2.
5. **[Level 5: Advanced Routing & Architecture](docs/05-advanced-routing-architecture.md)** - Microservices context, WebSockets, gRPC, TCP Streams.
6. **[Level 6: Logging, Monitoring & Debugging](docs/06-logging-monitoring-debugging.md)** - Custom logging formats (JSON), Prometheus integration, Real IP extraction.
7. **[Level 7: Production Deployment](docs/07-production-deployment.md)** - Zero-downtime reloads, Blue/Green strategies, Docker tuning.
8. **[Level 8: Interview Preparation](docs/08-interview-preparation.md)** - Real-world scenarios and system design for interviews.

## 🛠️ Hands-on Projects
The `/projects` directory contains isolated Docker Compose environments to practice the theory from the docs. 

### Prerequisites
- Docker Engine & Docker Compose
- OpenSSL (Optional: for generating test certificates using the provided scripts)

### Running the Projects
Navigate to any project directory and start the environment. For example:

```bash
cd projects/level-1-static-site
docker compose up -d
```

**Available Environments:**
* **Level 1 Static Site**: A basic site served directly by NGINX.
* **Level 2 Load Balancer**: NGINX routing traffic across two isolated backend containers using Round-Robin.
* **Level 3 HTTPS & Security**: Demonstrates HTTP to HTTPS redirects, SSL termination, and strict rate-limiting on an API endpoint. *(Requires running `generate-ssl.sh` first!)*
* **Level 4 Performance**: Showcases how `proxy_cache` can intercept and cache slow backend operations for immediate delivery.
* **Level 5 Microservices**: An API Gateway executing path-based routing to three different backend services (`/api/users`, `/api/orders`, `/api/search`).
* **Final Production Architecture**: The ultimate setup. Features modular configuration (`conf.d/`), complete SSL, upstream mapping, caching, upstream KeepAlive connections, rate-limiting, and hardened security settings. *(Requires running `generate-ssl.sh` first!)*

## 🔐 Setting up SSL for Local Testing
For projects requiring HTTPS (Level 3 and the Final Production setup), you must generate a self-signed certificate before spinning up the containers to avoid NGINX crashing due to missing files.

Inside those specific project directories, run the script:
```bash
./generate-ssl.sh
```
*(Or simply manually run the `openssl` command found inside the script if you are on Windows PowerShell).*

---
Happy Learning! 🛡️

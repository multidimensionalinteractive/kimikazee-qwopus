# Security Policy

Kimikazee Qwopus takes the security of our software seriously. This document outlines our security policy and vulnerability disclosure process.

---

## Table of Contents

- [Supported Versions](#supported-versions)
- [Reporting a Vulnerability](#reporting-a-vulnerability)
- [Security Best Practices](#security-best-practices)
- [Security Features](#security-features)
- [Incident Response](#incident-response)
- [Dependencies](#dependencies)

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported | End of Life |
|---------|-----------|-------------|
| 1.0.x | ✅ Yes | N/A |
| Older versions | ❌ No | N/A |

**Note:** Only the latest major version receives security updates. Please upgrade to version 1.0.x for security patches.

---

## Reporting a Vulnerability

We appreciate responsible disclosure of security vulnerabilities.

### How to Report

**⚠️ IMPORTANT:** Do NOT disclose vulnerabilities publicly before they have been addressed.

1. **Email:** `security@kimikazee.com`
2. **GitHub:** Create a [private security advisory](https://github.com/kimikazee/kimikazee-qwopus/security/advisories/new)
3. **PGP:** Use our PGP key for encrypted communications (see below)

### What to Include

Please provide the following information:

- **Type of vulnerability** (e.g., SQL injection, XSS, RCE)
- **Affected components** and version numbers
- **Detailed description** with steps to reproduce
- **Impact assessment** (what an attacker could achieve)
- **Proof of concept** (if available)
- **Suggested fix** (optional)
- **Your contact information** for follow-up

### PGP Key

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBF... (full key would be provided)

-----END PGP PUBLIC KEY BLOCK-----
```

### Response Timeline

We commit to the following response times:

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix development | Within 30 days (critical), 90 days (low severity) |
| Public disclosure | Coordinated with reporter |

### Security Updates

Security updates will be announced via:

- GitHub release notes
- Security advisory page
- Email to registered users (if applicable)

---

## Security Best Practices

### For Deployments

#### Network Security

1. **Firewall Configuration**
   ```bash
   # Only allow necessary ports
   ufw allow 8080/tcp
   ufw enable
   ```

2. **TLS/HTTPS**
   - Always use HTTPS in production
   - Configure proper TLS certificates
   - Redirect HTTP to HTTPS

3. **Reverse Proxy**
   ```nginx
   # Example nginx configuration
   server {
       listen 443 ssl http2;
       server_name qwopus.example.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       # Security headers
       add_header X-Frame-Options "DENY";
       add_header X-Content-Type-Options "nosniff";
       add_header X-XSS-Protection "1; mode=block";
       add_header Referrer-Policy "strict-origin-when-cross-origin";
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

#### Authentication & Authorization

1. **API Keys**
   ```bash
   # Set strong API key
   export API_KEY=$(openssl rand -base64 32)
   ```

2. **Rate Limiting**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   
   location /v1/ {
       limit_req zone=api burst=20 nodelay;
       proxy_pass http://localhost:8080;
   }
   ```

3. **Input Validation**
   - Sanitize all user inputs
   - Validate request parameters
   - Implement proper error handling

#### Container Security

1. **Run as Non-Root**
   ```dockerfile
   # Dockerfile example
   RUN adduser --disabled-password --gecos '' qwopus
   USER qwopus
   ```

2. **Resource Limits**
   ```yaml
   # Kubernetes example
   resources:
     requests:
       memory: "16Gi"
       cpu: "4000m"
     limits:
       memory: "24Gi"
       cpu: "8000m"
   ```

3. **Image Scanning**
   ```bash
   # Scan Docker image
   docker scan kimikazee/qwopus:latest
   ```

#### Environment Configuration

1. **Secrets Management**
   ```bash
   # Use environment variables
   export TELEGRAM_BOT_TOKEN="your-secret-token"
   export API_KEY="your-secret-key"
   ```

2. **Config File Permissions**
   ```bash
   # Restrict access to config
   chmod 600 config.yaml
   ```

3. **Log Security**
   ```yaml
   # config.yaml
   log_file: /secure/path/logs/agent.log
   log_level: INFO  # Avoid DEBUG in production
   ```

---

## Security Features

### Current Security Measures

- ✅ **Request Validation**: Pydantic models for type safety
- ✅ **Input Sanitization**: Basic input validation
- ✅ **Error Handling**: Graceful error responses without leaking sensitive data
- ✅ **CORS Configuration**: Configurable CORS policies
- ✅ **Structured Logging**: No sensitive data in logs
- ✅ **TLS Support**: Via reverse proxy
- ✅ **Non-Root Execution**: Docker containers run as non-root

### Security Headers

When properly configured with a reverse proxy:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | DENY | Prevent clickjacking |
| `X-Content-Type-Options` | nosniff | Prevent MIME sniffing |
| `X-XSS-Protection` | 1; mode=block | Enable XSS filter |
| `Content-Security-Policy` | (custom) | Control resource loading |
| `Strict-Transport-Security` | max-age=31536000 | Enforce HTTPS |

### Model Security

- ⚠️ **No Content Filtering**: This is an uncensored model
- ⚠️ **No Built-in Moderation**: Responsible use is user's responsibility
- ⚠️ **No Authentication**: Network-level security only

---

## Incident Response

### In Case of a Security Incident

1. **Immediate Actions**
   - Document the incident timeline
   - Preserve logs and evidence
   - Limit potential damage

2. **Contact Us**
   - Email: `security@kimikazee.com`
   - Provide incident details

3. **Response Steps**
   - We will acknowledge within 48 hours
   - Assess severity and impact
   - Develop and test fix
   - Deploy security update
   - Communicate resolution

### Known Issues

| Issue | Status | Workaround |
|-------|--------|------------|
| No built-in authentication | Not fixed | Use reverse proxy |
| No rate limiting | Not fixed | Use reverse proxy |
| No content filtering | By design | Implement externally |

---

## Dependencies

### Third-Party Security

We use several third-party libraries. Security updates are monitored:

| Package | Purpose | Version |
|---------|---------|---------|
| FastAPI | Web framework | >= 0.104.0 |
| Pydantic | Validation | >= 2.5.0 |
| uvicorn | ASGI server | >= 0.24.0 |
| llama-cpp-python | Inference | >= 0.2.17 |
| PyYAML | Configuration | >= 6.0 |

### Dependency Monitoring

- **Automated Scanning**: GitHub Dependabot
- **Regular Audits**: Monthly security reviews
- **Vulnerability Database**: Integrated with safety and bandit

### Reporting Dependency Vulnerabilities

If you discover a vulnerability in a dependency:

1. Check if it's already reported
2. Report to the upstream project
3. Notify us at `security@kimikazee.com` if it affects our usage

---

## Responsible Disclosure

We encourage responsible disclosure of security issues:

1. **Give us time to respond**: We commit to 30 days for critical fixes
2. **Provide details**: Clear reproduction steps help us fix issues faster
3. **Allow coordination**: Work with us on timing of public disclosure
4. **Respect privacy**: Do not expose user data

---

## Security Updates

Security updates will be published as:

1. **GitHub Releases**: With security patch notes
2. **Advisories**: GitHub Security Advisories
3. **Email Notifications**: For registered users

---

## License

This security policy is part of Kimikazee Qwopus, licensed under MIT.

---

## Contact

- **Security Email:** `security@kimikazee.com`
- **GitHub:** [kimikazee/kimikazee-qwopus](https://github.com/kimikazee/kimikazee-qwopus)
- **Security Advisories:** [GitHub Security Tab](https://github.com/kimikazee/kimikazee-qwopus/security)

---

*Last updated: 2026-04-30 | Version: 1.0.0*

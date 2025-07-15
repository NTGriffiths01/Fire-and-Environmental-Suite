# Fire and Environmental Safety Suite

A production-grade, secure, and audit-compliant full-stack web application for the Massachusetts Department of Correction (MADOC) to support documentation, compliance, inspection, and correctional facility asset tracking needs governed by ICC, ACA, and 105 CMR 451.

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React 18 + Tailwind CSS + TypeScript
- **Backend**: FastAPI (Python 3.11) + PostgreSQL + MongoDB
- **Authentication**: JWT with Azure AD integration
- **File Storage**: AWS S3 with 7-year retention
- **Email**: AWS SES for notifications
- **PDF Generation**: WeasyPrint
- **Infrastructure**: AWS GovCloud + Terraform
- **CI/CD**: GitHub Actions
- **Monitoring**: CloudWatch + Audit logging

### Security Features
- Role-based access control (Admin, Inspector, Deputy of Operations)
- OAuth2 JWT authentication with Azure AD
- AES-256 encryption at rest
- TLS 1.2+ encryption in transit
- Comprehensive audit logging
- Rate limiting and DDoS protection
- Security headers and CSP

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and Yarn
- Python 3.11+
- AWS CLI configured
- Terraform 1.6+

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/madoc/fire-safety-suite.git
   cd fire-safety-suite
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec backend python -m alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

### Default Credentials
- **Admin**: admin@madoc.gov / admin123
- **Inspector**: inspector@madoc.gov / inspector123
- **Deputy**: deputy@madoc.gov / deputy123

## 📋 Features

### Core Modules

#### 1. Authentication & Authorization
- Azure AD integration with OAuth2 flow
- JWT token-based session management
- Role-based access control
- Multi-factor authentication support

#### 2. Dashboard
- **Admin Dashboard**: User management, template uploads, system stats, audit logs
- **Inspector Dashboard**: Create inspections, manage drafts, view status
- **Deputy Dashboard**: Review queue, approve/reject inspections, generate reports

#### 3. Inspection Management
- Dynamic form rendering from JSON templates
- Real-time citation suggestions (ICC, ACA, 105 CMR 451)
- File attachments with S3 storage
- Draft saving and submission workflow
- Digital signatures with timestamping

#### 4. PDF Generation
- Professional inspection reports
- Facility information and violations
- Citation details and signatures
- Automatic archival to S3

#### 5. Audit & Compliance
- Comprehensive action logging
- PostgreSQL audit trail
- CloudWatch log streaming
- Compliance reporting

### Security & Compliance

#### Role Permissions
- **Admin**: Full system access, user management, template creation
- **Inspector**: Create/edit inspections, view own reports
- **Deputy**: Review inspections, approve/reject, generate PDFs

#### Data Protection
- All data encrypted at rest (AES-256)
- TLS 1.2+ for data in transit
- 7-year retention policy for files
- Audit trail for all actions

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/fire_safety_suite
MONGO_URL=mongodb://localhost:27017/fire_safety_suite

# Authentication
SECRET_KEY=your-secret-key-here
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id

# AWS Services
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=fire-safety-files
AWS_SES_REGION=us-east-1
SENDER_EMAIL=noreply@madoc.gov

# Security
ENCRYPTION_KEY=your-encryption-key
```

#### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_AZURE_AD_CLIENT_ID=your-client-id
REACT_APP_AZURE_AD_TENANT_ID=your-tenant-id
```

## 🏭 Production Deployment

### AWS Infrastructure

1. **Configure AWS CLI**
   ```bash
   aws configure --profile govcloud
   ```

2. **Deploy infrastructure**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Deploy application**
   ```bash
   # Build and push images
   docker build -t fire-safety-frontend ./frontend
   docker build -t fire-safety-backend ./backend
   
   # Push to ECR
   aws ecr get-login-password --region us-gov-west-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-gov-west-1.amazonaws.com
   docker tag fire-safety-frontend:latest <account>.dkr.ecr.us-gov-west-1.amazonaws.com/fire-safety-frontend:latest
   docker push <account>.dkr.ecr.us-gov-west-1.amazonaws.com/fire-safety-frontend:latest
   ```

### CI/CD Pipeline

The GitHub Actions workflow automatically:
- Runs tests and security scans
- Builds and pushes Docker images
- Deploys to AWS ECS
- Updates infrastructure with Terraform
- Sends deployment notifications

## 🧪 Testing

### Run Tests
```bash
# Backend tests
cd backend
python -m pytest tests/ -v --cov=.

# Frontend tests
cd frontend
yarn test --coverage

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Security Testing
```bash
# Vulnerability scanning
trivy fs .

# SAST scanning
bandit -r backend/

# Dependency scanning
safety check -r backend/requirements.txt
```

## 📊 Monitoring & Observability

### Metrics
- Application performance metrics
- Database query performance
- File upload/download metrics
- Authentication success/failure rates

### Logging
- Structured JSON logging
- Audit trail for all actions
- Error tracking and alerting
- Performance monitoring

### Alerting
- Failed authentication attempts
- System errors and exceptions
- Performance degradation
- Security incidents

## 🔐 Security Considerations

### Data Protection
- All PII encrypted at rest
- Audit logs immutable
- Regular security assessments
- Penetration testing

### Access Control
- Least privilege principle
- Regular access reviews
- Multi-factor authentication
- Session management

### Compliance
- NIST Cybersecurity Framework
- FISMA compliance
- SOC 2 Type II controls
- Regular compliance audits

## 📚 API Documentation

### Authentication
```bash
# Login
POST /api/auth/login
Content-Type: application/json
{
  "email": "admin@madoc.gov",
  "password": "admin123"
}

# Get current user
GET /api/auth/me
Authorization: Bearer <token>
```

### Inspections
```bash
# Create inspection
POST /api/inspections
Authorization: Bearer <token>
Content-Type: application/json
{
  "template_id": "template-uuid",
  "facility_id": "facility-uuid",
  "form_data": {}
}

# Get inspections
GET /api/inspections
Authorization: Bearer <token>
```

### Templates
```bash
# Create template
POST /api/templates
Authorization: Bearer <token>
Content-Type: application/json
{
  "name": "Monthly Fire Safety",
  "description": "Standard monthly inspection",
  "template_data": {...}
}
```

## 🛠️ Development

### Code Style
- Backend: Black + isort + flake8
- Frontend: Prettier + ESLint
- Pre-commit hooks for formatting

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Features
1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Update documentation
5. Submit pull request

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please contact:
- **Technical Issues**: tech-support@madoc.gov
- **Security Issues**: security@madoc.gov
- **General Questions**: fire-safety@madoc.gov

## 📈 Roadmap

- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Machine learning for predictive maintenance
- [ ] Integration with building management systems
- [ ] Real-time monitoring sensors

---

**Massachusetts Department of Correction - Fire and Environmental Safety Division**
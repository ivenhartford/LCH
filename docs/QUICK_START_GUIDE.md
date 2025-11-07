# Lenox Cat Hospital - Quick Start Guide

**Get started in 5 minutes!** | Last Updated: 2025-11-07

This quick start guide will get you up and running with the Lenox Cat Hospital Practice Management System in just a few minutes.

---

## 🚀 For End Users (Staff)

### Step 1: Log In

1. Open your web browser
2. Navigate to your clinic's URL (provided by your administrator)
3. Enter your username and password
4. Click **Login**

**First time?** Contact your administrator to create your account.

### Step 2: Explore the Dashboard

After logging in, you'll see the **Dashboard** with:

- **Quick Stats** - See today's appointments, total clients, and active patients
- **Today's Appointments** - Color-coded schedule for the day
- **Recent Patients** - Quick access to recently seen patients
- **Quick Actions** - Buttons to create new clients, patients, appointments, and visits

### Step 3: Common Tasks

#### Schedule an Appointment

1. Click **Calendar** in the sidebar (or **New Appointment** button)
2. Click a time slot on the calendar
3. Fill in the appointment form:
   - Select the client
   - Select the patient (filtered by chosen client)
   - Choose appointment type (Wellness, Urgent Care, Surgery, etc.)
   - Add any notes
4. Click **Save**

**Tip:** Appointments are color-coded by type for easy viewing!

#### Add a New Client & Patient

1. Click **Clients** → **Add Client**
2. Fill in client information:
   - Full name, email, phone
   - Address
   - Communication preferences
3. Click **Save**
4. On the client's profile, click **Add Patient**
5. Fill in patient details:
   - Name, species, breed, gender
   - Date of birth, weight
   - Microchip number, insurance info
6. Click **Save**

#### Create a Visit (Clinical Workflow)

1. Click **Visits** → **New Visit**
2. Select the patient
3. Choose visit type (Wellness Exam, Sick Visit, Surgery, etc.)
4. Add SOAP notes:
   - **Subjective:** Chief complaint, history
   - **Objective:** Physical exam findings, vital signs
   - **Assessment:** Diagnosis
   - **Plan:** Treatment plan, follow-up
5. Add vital signs, diagnoses, vaccinations as needed
6. Click **Save**

#### Create an Invoice

1. Navigate to the visit or patient you want to bill
2. Click **Create Invoice**
3. Add line items (services/products):
   - Click **Add Item**
   - Select from service catalog
   - Adjust quantity and price if needed
4. Review total and tax
5. Click **Save & Send** to create the invoice

#### Process a Payment

1. Go to **Invoices** and open an invoice
2. Click **Add Payment**
3. Enter:
   - Payment amount
   - Payment method (Cash, Card, Check, etc.)
   - Reference number (optional)
4. Click **Save**

**Note:** Invoice status updates automatically (Partial, Paid, etc.)

### Step 4: Global Search

Press **Ctrl+K** (or **Cmd+K** on Mac) to open the global search:
- Search for clients, patients, appointments, or invoices
- Type a few letters and see instant results
- Click any result to navigate directly

### Need Help?

- 📖 **Full User Guide:** See the comprehensive [USER_GUIDE.md](./USER_GUIDE.md)
- 🛠️ **Technical Issues:** Contact your system administrator
- 💡 **Tips:** Hover over any field for tooltips and help text

---

## 🔧 For Administrators

### Initial Setup

#### 1. Installation & Deployment

**Using Docker (Recommended):**

```bash
# Clone the repository
git clone https://github.com/yourusername/LCH.git
cd LCH

# Copy environment file and configure
cp .env.production .env
nano .env  # Edit configuration (see below)

# Deploy the application
./scripts/deploy.sh production
```

**Required Environment Variables:**

```bash
# Security (REQUIRED)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
POSTGRES_PASSWORD=<strong-database-password>

# Domain (for production)
DOMAIN_NAME=clinic.example.com
SSL_EMAIL=admin@example.com

# Database
POSTGRES_DB=vet_clinic_db
POSTGRES_USER=vet_clinic_user

# Application
FLASK_ENV=production
GUNICORN_WORKERS=4
```

**Generate a strong SECRET_KEY:**

```bash
openssl rand -hex 32
```

#### 2. SSL/HTTPS Setup (Production)

```bash
# Initialize SSL certificates (Let's Encrypt)
./scripts/init-ssl.sh
```

This script will:
- Obtain SSL certificates from Let's Encrypt
- Configure nginx for HTTPS
- Set up automatic renewal

**Requirements:**
- Domain name pointing to your server's IP
- Ports 80 and 443 open to the internet

#### 3. Create Initial Admin User

After deployment, create your first admin user:

```bash
# Access the backend container
docker-compose exec backend bash

# Create admin user
flask create-admin <username> <email>
```

Or set environment variables before deployment:

```bash
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=temporary-password
INITIAL_ADMIN_ROLE=administrator
```

**⚠️ IMPORTANT:** Change the initial admin password immediately after first login!

### Daily Operations

#### Database Backups

**Manual Backup:**

```bash
./scripts/backup.sh
```

**List Available Backups:**

```bash
./scripts/list-backups.sh
```

**Restore from Backup:**

```bash
./scripts/restore.sh backup_vet_clinic_db_20250107_140000.sql.gz
```

**Automatic Backups:**

Backups run daily at 2 AM automatically (configured in docker-compose.prod.yml).
- Retention: 30 days (configurable)
- Location: `/backups` volume
- Compression: gzip

#### Application Updates

**Update to Latest Version:**

```bash
./scripts/update.sh production
```

This performs a zero-downtime rolling update:
1. Creates pre-update backup
2. Pulls latest code (if using git)
3. Builds new images
4. Performs rolling update
5. Runs database migrations
6. Restarts services

#### Monitoring & Logs

**View Service Logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

**View Audit Logs:**

```bash
# Access audit log file
docker-compose exec backend cat /app/logs/audit.log

# Follow audit log in real-time
docker-compose exec backend tail -f /app/logs/audit.log

# Search audit logs
docker-compose exec backend grep "patient_created" /app/logs/audit.log
```

**Check Service Health:**

```bash
docker-compose ps
```

**Resource Usage:**

```bash
docker stats
```

### User Management

#### Create New Staff User

1. Log in as administrator
2. Go to **Staff Management**
3. Click **Add Staff Member**
4. Fill in:
   - Name, email, phone
   - Role (Veterinarian, Technician, Receptionist, etc.)
   - Permissions (prescribe, perform surgery, access billing)
   - Username and initial password
5. Click **Save**
6. Provide credentials to the new user

**User Roles:**
- **Administrator:** Full system access
- **Veterinarian:** Clinical access, prescriptions, medical records
- **Technician:** Clinical access, limited prescriptions
- **Receptionist:** Appointments, invoicing, client management

### Security Checklist

- [ ] Strong `SECRET_KEY` configured (32+ characters)
- [ ] Strong database password set
- [ ] SSL/HTTPS enabled for production
- [ ] Initial admin password changed
- [ ] Firewall configured (ports 80, 443 only)
- [ ] Regular backups running (verify daily)
- [ ] User accounts have strong passwords
- [ ] Staff accounts have appropriate role permissions
- [ ] Audit logs are being generated
- [ ] System updates applied monthly

### Performance Tuning

**For High-Traffic Clinics:**

Edit `.env` file:

```bash
# Increase Gunicorn workers (CPU cores * 2 + 1)
GUNICORN_WORKERS=8

# Increase worker timeout for long requests
GUNICORN_TIMEOUT=180

# Increase PostgreSQL resources in docker-compose.prod.yml
# (memory, CPU limits)
```

**Database Optimization:**

Database indexes are already configured (60+ indexes).
For very large datasets:

```bash
# Vacuum and analyze database
docker-compose exec postgres vacuumdb -U vet_clinic_user -d vet_clinic_db --analyze
```

### Troubleshooting

**Application won't start:**

```bash
# Check container logs
docker-compose logs backend frontend postgres

# Verify environment variables
docker-compose config

# Restart all services
docker-compose down && docker-compose up -d
```

**Database connection errors:**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Test database connection
docker-compose exec postgres psql -U vet_clinic_user -d vet_clinic_db -c "SELECT version();"
```

**SSL certificate issues:**

```bash
# Check certificate status
docker-compose run --rm certbot certificates

# Manually renew certificate
docker-compose run --rm certbot renew
```

**Performance issues:**

```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.prod.yml
# Review application logs for slow queries
docker-compose logs backend | grep "WARNING"
```

### Support & Resources

- 📖 **Full Admin Guide:** [ADMIN_GUIDE.md](./ADMIN_GUIDE.md)
- 🔐 **Security Guide:** [SECURITY.md](./SECURITY.md)
- 🐳 **Docker Guide:** [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
- 🗺️ **Development Roadmap:** [ROADMAP.md](./ROADMAP.md)
- 🏗️ **Data Models:** [DATA_MODELS.md](./DATA_MODELS.md)

---

## Common Issues & Solutions

### Issue: "SECRET_KEY is required"

**Solution:** Set a strong SECRET_KEY in `.env`:

```bash
# Generate key
SECRET_KEY=$(openssl rand -hex 32)

# Add to .env
echo "SECRET_KEY=${SECRET_KEY}" >> .env
```

### Issue: "Database connection failed"

**Solution:** Verify PostgreSQL is running and credentials are correct:

```bash
# Check if running
docker-compose ps postgres

# Verify credentials in .env match docker-compose.yml
```

### Issue: "Permission denied" when running scripts

**Solution:** Make scripts executable:

```bash
chmod +x scripts/*.sh
```

### Issue: Cannot access application from browser

**Solution:**
1. Check firewall allows ports 80/443
2. Verify containers are running: `docker-compose ps`
3. Check if domain DNS is configured correctly: `dig yourdomain.com`

---

## Next Steps

✅ **Deployment Complete?** See [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) for advanced administration

✅ **Training Staff?** Share the [USER_GUIDE.md](./USER_GUIDE.md) with your team

✅ **Customization?** Review [FEATURES.md](./FEATURES.md) and [ROADMAP_Part_2.md](./ROADMAP_Part_2.md)

✅ **Questions?** Check the full documentation in the `docs/` folder

---

**Version:** 1.0
**Last Updated:** 2025-11-07
**Support:** Contact your system administrator

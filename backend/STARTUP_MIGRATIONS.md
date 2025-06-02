# Automatic Database Migrations at Startup

The CrewAI Backend now automatically runs database migrations when the application starts up. This ensures that the database schema is always up to date without requiring manual intervention.

## How It Works

When the FastAPI application starts, it will:

1. **Test Database Connection**: Verify that the database is accessible
2. **Check Migration Status**: Compare current database revision with latest available migrations
3. **Initialize Migration Tracking**: Set up Alembic migration tracking if not present
4. **Run Migrations**: Apply any pending migrations automatically
5. **Verify Success**: Confirm that migrations completed successfully

## Configuration

### Environment Variables

Add these variables to your `.env` file to control migration behavior:

```bash
# Enable/disable automatic migrations at startup (default: true)
AUTO_MIGRATE_ON_STARTUP=true

# Whether to fail startup if migrations fail (default: true)
FAIL_ON_MIGRATION_ERROR=true
```

### Migration Modes

#### 1. Automatic Migration (Default)
```bash
AUTO_MIGRATE_ON_STARTUP=true
FAIL_ON_MIGRATION_ERROR=true
```
- Migrations run automatically at startup
- Application fails to start if migrations fail
- **Recommended for development and production**

#### 2. Check-Only Mode
```bash
AUTO_MIGRATE_ON_STARTUP=false
FAIL_ON_MIGRATION_ERROR=true
```
- Checks for pending migrations but doesn't run them
- Logs warnings if migrations are needed
- Application starts normally
- **Useful for environments where migrations are run separately**

#### 3. Permissive Mode
```bash
AUTO_MIGRATE_ON_STARTUP=true
FAIL_ON_MIGRATION_ERROR=false
```
- Attempts to run migrations
- Application starts even if migrations fail
- **Use with caution - some database operations may fail**

## Safety Features

### Data Protection
- **Backward Compatible**: Migrations are designed to preserve existing data
- **Incremental**: Only applies migrations that haven't been run yet
- **Transactional**: Each migration runs in a transaction where possible
- **Rollback Ready**: Failed migrations can be rolled back using Alembic commands

### Error Handling
- **Connection Testing**: Verifies database connectivity before attempting migrations
- **Revision Tracking**: Maintains accurate migration state tracking
- **Detailed Logging**: Provides comprehensive logs of migration activities
- **Graceful Failure**: Clear error messages when migrations fail

## Monitoring and Troubleshooting

### Health Check Endpoints

The application provides endpoints to monitor database and migration status:

#### Basic Health Check
```http
GET /health
```
Returns basic application and database health status.

#### Detailed Database Status
```http
GET /db-status
```
Returns detailed information including:
- Database connection status
- Current migration revision
- Latest available migration
- Whether migrations are up to date

### Manual Migration Commands

If you need to run migrations manually, use the database management script:

```bash
# Run migrations to latest
python manage_db.py migrate

# Check current status
python manage_db.py status

# View migration history
python manage_db.py history

# Reset database (development only)
python manage_db.py reset
```

### Testing Startup Functionality

Use the test script to verify startup functionality:

```bash
python test_startup.py
```

## Production Deployment

### Recommended Configuration

For production deployments:

```bash
# .env
AUTO_MIGRATE_ON_STARTUP=true
FAIL_ON_MIGRATION_ERROR=true
DATABASE_URL=postgresql://user:password@host:port/database
```

### Deployment Strategy

1. **Blue-Green Deployment**: Run migrations on the new environment before switching traffic
2. **Rolling Updates**: Ensure migrations are backward compatible for zero-downtime deployments
3. **Backup First**: Always backup the database before running migrations in production

### Monitoring

Monitor these aspects in production:
- Application startup time (migrations may add delay)
- Migration success/failure rates
- Database connection health
- Application logs for migration warnings

## Development Workflow

1. **Create Migration**: When you modify models, generate a migration:
   ```bash
   python manage_db.py generate "Description of changes"
   ```

2. **Test Locally**: The migration will run automatically when you restart the application

3. **Review Migration**: Check the generated migration file in `alembic/versions/`

4. **Commit Changes**: Include both model changes and migration files in your commit

5. **Deploy**: The migration will run automatically on deployment

## Common Issues and Solutions

### Issue: Migration Fails on Startup
**Solution**: Check the logs for specific error details, then either fix the migration or run manual troubleshooting.

### Issue: Application Won't Start Due to Database Connection
**Solution**: Verify DATABASE_URL and ensure database server is running.

### Issue: Migration Seems Stuck
**Solution**: Check if there are conflicting migrations or if the database is locked.

### Issue: Need to Skip Automatic Migrations
**Solution**: Set `AUTO_MIGRATE_ON_STARTUP=false` temporarily.

## Security Considerations

- Database credentials are masked in logs
- Migration files should be reviewed before deployment
- Consider running migrations in a separate step for sensitive environments
- Ensure database user has appropriate migration permissions

## See Also

- [`manage_db.py`](./manage_db.py) - Manual database management
- [`startup.py`](./startup.py) - Startup migration implementation
- [`test_startup.py`](./test_startup.py) - Startup functionality tests
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Migration framework 
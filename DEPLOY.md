# Deployment Guide for PythonAnywhere

## 1. Sign Up for PythonAnywhere
1. Go to [PythonAnywhere](https://www.pythonanywhere.com)
2. Sign up for a "Hacker" account ($5/month)
   - Provides custom domains
   - Better performance
   - More storage

## 2. Initial Setup
1. Open a Bash console in PythonAnywhere
2. Clone the repository:
```bash
git clone https://github.com/cdobratz/family-recipe-app.git
cd family-recipe-app
git checkout family  # Switch to family branch
```

## 3. Set Up Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.10 family-env
pip install -r requirements.txt
```

## 4. Configure Web App
1. Go to the Web tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Set the following configurations:
   - Source code: /home/yourusername/family-site
   - Working directory: /home/yourusername/family-site
   - Virtual environment: /home/yourusername/.virtualenvs/family-env

## 5. Configure WSGI File
1. Click on the WSGI configuration file link
2. Replace the contents with the contents of pa_wsgi.py
3. Update the following in the file:
   - Change 'yourusername' to your PythonAnywhere username
   - Set a secure SECRET_KEY

## 6. Static Files
Add these static file mappings in the Web tab:
- URL: /static/
  Directory: /home/yourusername/family-site/static/

## 7. Environment Variables
Add these environment variables in the Web tab:
```
PRODUCTION=true
FLASK_DEBUG=false
SECRET_KEY=your-secure-key-here
```

## 8. Database Setup
```bash
# In PythonAnywhere bash console
cd family-site
python init_db.py
python create_test_user.py  # If needed
```

## 9. Scheduled Tasks
Set up daily database backups:
1. Go to the Tasks tab
2. Add a daily task:
```bash
cp /home/yourusername/family-site/instance/recipe_app.db /home/yourusername/backups/recipe_app_$(date +%Y%m%d).db
```

## 10. SSL/HTTPS Setup
1. Go to the Web tab
2. Enable HTTPS
3. Force HTTPS by checking "Force HTTPS"

## 11. Domain Setup (Optional)
1. Register your domain
2. Go to the Web tab
3. Add your custom domain
4. Update your domain's DNS settings

## Maintenance

### Database Backups
Backups are stored in ~/backups/
Download them periodically via SFTP/SCP

### Updates
To update the application:
```bash
cd family-site
git pull origin family
python -m pip install -r requirements.txt
touch /var/www/yourusername_pythonanywhere_com_wsgi.py  # Reload the application
```

### Monitoring
- Check the error logs in the Web tab
- Monitor disk space usage
- Review access logs periodically

## Support
- PythonAnywhere help: https://help.pythonanywhere.com/
- Flask documentation: https://flask.palletsprojects.com/

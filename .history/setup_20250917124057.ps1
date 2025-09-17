# PowerShell setup script for Windows
Write-Host "🏥 Setting up Medi-Tour API on Windows..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Try different installation strategies
Write-Host "⬇️ Installing dependencies..." -ForegroundColor Yellow

# Strategy 1: Try minimal requirements first
Write-Host "🎯 Trying minimal installation..." -ForegroundColor Cyan
$minimalInstall = $false
try {
    pip install -r requirements-minimal.txt
    $minimalInstall = $true
    Write-Host "✅ Minimal installation successful!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Minimal installation failed, trying Windows-specific requirements..." -ForegroundColor Yellow
}

# Strategy 2: Try Windows requirements if minimal failed
if (-not $minimalInstall) {
    try {
        pip install -r requirements-windows.txt
        Write-Host "✅ Windows-specific installation successful!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Windows requirements failed, trying individual packages..." -ForegroundColor Yellow
        
        # Strategy 3: Install packages individually
        $packages = @(
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0", 
            "sqlalchemy==2.0.23",
            "alembic==1.13.0",
            "pydantic==2.4.2",
            "python-dotenv==1.0.0",
            "aiosqlite==0.19.0"
        )
        
        foreach ($package in $packages) {
            try {
                pip install $package
                Write-Host "✅ Installed $package" -ForegroundColor Green
            } catch {
                Write-Host "❌ Failed to install $package" -ForegroundColor Red
            }
        }
    }
}

# Setup environment file
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.windows" ".env"
    Write-Host "⚠️ Please update .env with your database credentials if needed" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Test the installation
Write-Host "🧪 Testing installation..." -ForegroundColor Yellow
try {
    python -c "import fastapi, sqlalchemy, pydantic; print('✅ Core packages imported successfully')"
} catch {
    Write-Host "❌ Import test failed. Some packages may not be properly installed." -ForegroundColor Red
}

# Initialize database migrations (with SQLite by default)
Write-Host "🗄️ Initializing database migrations..." -ForegroundColor Yellow
try {
    alembic revision --autogenerate -m "Initial migration"
    Write-Host "✅ Database migration created!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Migration creation failed. You can run this manually later." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. The app is configured to use SQLite by default (no database setup needed)" -ForegroundColor White
Write-Host "2. If you want PostgreSQL/MySQL, update the DATABASE_URL in .env" -ForegroundColor White
Write-Host "3. Run migrations: alembic upgrade head" -ForegroundColor White
Write-Host "4. Start the server: uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation will be available at: http://localhost:8000/docs" -ForegroundColor Green
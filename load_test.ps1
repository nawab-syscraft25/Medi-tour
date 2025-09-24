# PowerShell Load Test Script for Medi-Tour API
# Simple load testing using Invoke-RestMethod

param(
    [string]$BaseUrl = "http://165.22.223.163:8000",
    [int]$ConcurrentUsers = 5,
    [int]$RequestsPerUser = 10
)

Write-Host "🚀 Starting Load Tests for Medi-Tour API" -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "Concurrent Users: $ConcurrentUsers" -ForegroundColor Cyan
Write-Host "Requests per User: $RequestsPerUser" -ForegroundColor Cyan
Write-Host "=" * 50

# Function to make HTTP request and measure time
function Test-Endpoint {
    param(
        [string]$Endpoint,
        [string]$TestName,
        [int]$Concurrent = 5,
        [int]$TotalRequests = 25
    )
    
    Write-Host ""
    Write-Host "🔄 Testing: $TestName" -ForegroundColor Yellow
    Write-Host "Endpoint: $Endpoint" -ForegroundColor Gray
    Write-Host "Total Requests: $TotalRequests" -ForegroundColor Gray
    Write-Host "-" * 30
    
    $StartTime = Get-Date
    $Results = @()
    $Jobs = @()
    
    # Create script block for each request
    $ScriptBlock = {
        param($Url)
        try {
            $RequestStart = Get-Date
            $Response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30
            $RequestEnd = Get-Date
            $ResponseTime = ($RequestEnd - $RequestStart).TotalMilliseconds
            
            return @{
                Success = $true
                ResponseTime = $ResponseTime
                StatusCode = 200
                Error = $null
            }
        }
        catch {
            $RequestEnd = Get-Date
            $ResponseTime = ($RequestEnd - $RequestStart).TotalMilliseconds
            
            return @{
                Success = $false
                ResponseTime = $ResponseTime
                StatusCode = 0
                Error = $_.Exception.Message
            }
        }
    }
    
    # Start concurrent jobs
    $RequestsPerBatch = [math]::Ceiling($TotalRequests / $Concurrent)
    
    for ($batch = 0; $batch -lt $Concurrent; $batch++) {
        $BatchRequests = if (($batch + 1) * $RequestsPerBatch -gt $TotalRequests) { 
            $TotalRequests - ($batch * $RequestsPerBatch)
        } else { 
            $RequestsPerBatch 
        }
        
        for ($i = 0; $i -lt $BatchRequests; $i++) {
            $Job = Start-Job -ScriptBlock $ScriptBlock -ArgumentList "$BaseUrl$Endpoint"
            $Jobs += $Job
        }
    }
    
    # Wait for all jobs to complete and collect results
    $Results = $Jobs | Wait-Job | Receive-Job
    $Jobs | Remove-Job
    
    $EndTime = Get-Date
    $TotalTime = ($EndTime - $StartTime).TotalSeconds
    
    # Calculate statistics
    $SuccessfulRequests = ($Results | Where-Object { $_.Success }).Count
    $FailedRequests = $Results.Count - $SuccessfulRequests
    $SuccessRate = if ($Results.Count -gt 0) { ($SuccessfulRequests / $Results.Count) * 100 } else { 0 }
    $RequestsPerSecond = if ($TotalTime -gt 0) { $Results.Count / $TotalTime } else { 0 }
    
    $ResponseTimes = $Results | Where-Object { $_.Success } | Select-Object -ExpandProperty ResponseTime
    $AvgResponseTime = if ($ResponseTimes.Count -gt 0) { ($ResponseTimes | Measure-Object -Average).Average } else { 0 }
    $MinResponseTime = if ($ResponseTimes.Count -gt 0) { ($ResponseTimes | Measure-Object -Minimum).Minimum } else { 0 }
    $MaxResponseTime = if ($ResponseTimes.Count -gt 0) { ($ResponseTimes | Measure-Object -Maximum).Maximum } else { 0 }
    
    # Display results
    Write-Host "Results:" -ForegroundColor Green
    Write-Host "  Total requests: $($Results.Count)" -ForegroundColor White
    Write-Host "  Successful: $SuccessfulRequests" -ForegroundColor Green
    Write-Host "  Failed: $FailedRequests" -ForegroundColor Red
    Write-Host "  Success rate: $([math]::Round($SuccessRate, 2))%" -ForegroundColor White
    Write-Host "  Total time: $([math]::Round($TotalTime, 2))s" -ForegroundColor White
    Write-Host "  Requests/second: $([math]::Round($RequestsPerSecond, 2))" -ForegroundColor White
    Write-Host "  Avg response time: $([math]::Round($AvgResponseTime, 2))ms" -ForegroundColor White
    Write-Host "  Min response time: $([math]::Round($MinResponseTime, 2))ms" -ForegroundColor White
    Write-Host "  Max response time: $([math]::Round($MaxResponseTime, 2))ms" -ForegroundColor White
    
    return @{
        TestName = $TestName
        TotalRequests = $Results.Count
        SuccessfulRequests = $SuccessfulRequests
        FailedRequests = $FailedRequests
        SuccessRate = $SuccessRate
        TotalTime = $TotalTime
        RequestsPerSecond = $RequestsPerSecond
        AvgResponseTime = $AvgResponseTime
    }
}

# Test scenarios
Write-Host ""
Write-Host "Starting test scenarios..." -ForegroundColor Cyan

$AllResults = @()

# Test 1: Doctors endpoint
$AllResults += Test-Endpoint -Endpoint "/api/v1/doctors?skip=0&limit=10" -TestName "Doctors List" -Concurrent $ConcurrentUsers -TotalRequests ($ConcurrentUsers * $RequestsPerUser)

# Test 2: Hospitals endpoint  
$AllResults += Test-Endpoint -Endpoint "/api/v1/hospitals?skip=0&limit=10" -TestName "Hospitals List" -Concurrent $ConcurrentUsers -TotalRequests ($ConcurrentUsers * $RequestsPerUser)

# Test 3: Treatments endpoint
$AllResults += Test-Endpoint -Endpoint "/api/v1/treatments?skip=0&limit=10" -TestName "Treatments List" -Concurrent $ConcurrentUsers -TotalRequests ($ConcurrentUsers * $RequestsPerUser)

# Test 4: Filter endpoints
$AllResults += Test-Endpoint -Endpoint "/api/filters/locations" -TestName "Locations Filter" -Concurrent 3 -TotalRequests 15

$AllResults += Test-Endpoint -Endpoint "/api/filters/treatment-types" -TestName "Treatment Types Filter" -Concurrent 3 -TotalRequests 15

$AllResults += Test-Endpoint -Endpoint "/api/filters/specializations" -TestName "Specializations Filter" -Concurrent 3 -TotalRequests 15

# Test 5: High load test
$AllResults += Test-Endpoint -Endpoint "/api/v1/doctors?skip=0&limit=5" -TestName "High Load Test" -Concurrent ($ConcurrentUsers * 2) -TotalRequests ($ConcurrentUsers * $RequestsPerUser * 2)

# Summary
Write-Host ""
Write-Host "🏁 Load Testing Summary" -ForegroundColor Green
Write-Host "=" * 50

$TotalRequests = ($AllResults | Measure-Object -Property TotalRequests -Sum).Sum
$TotalSuccessful = ($AllResults | Measure-Object -Property SuccessfulRequests -Sum).Sum
$TotalFailed = ($AllResults | Measure-Object -Property FailedRequests -Sum).Sum
$OverallSuccessRate = if ($TotalRequests -gt 0) { ($TotalSuccessful / $TotalRequests) * 100 } else { 0 }

Write-Host "Total Tests: $($AllResults.Count)" -ForegroundColor White
Write-Host "Total Requests: $TotalRequests" -ForegroundColor White
Write-Host "Total Successful: $TotalSuccessful" -ForegroundColor Green
Write-Host "Total Failed: $TotalFailed" -ForegroundColor Red
Write-Host "Overall Success Rate: $([math]::Round($OverallSuccessRate, 2))%" -ForegroundColor White

# Best and worst performing tests
$BestTest = $AllResults | Sort-Object RequestsPerSecond -Descending | Select-Object -First 1
$WorstTest = $AllResults | Sort-Object RequestsPerSecond | Select-Object -First 1

Write-Host ""
Write-Host "🏆 Best Performance: $($BestTest.TestName) ($([math]::Round($BestTest.RequestsPerSecond, 2)) req/s)" -ForegroundColor Green
Write-Host "🐌 Worst Performance: $($WorstTest.TestName) ($([math]::Round($WorstTest.RequestsPerSecond, 2)) req/s)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Load testing completed!" -ForegroundColor Green
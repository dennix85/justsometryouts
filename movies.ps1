# Media Collection Analyzer
# This script analyzes media files, checks for encoding issues, and creates an HTML dashboard

# Function to show a simple GUI for folder selection
function Show-FolderBrowserDialog {
    param (
        [string]$Description = "Select a folder"
    )
    
    Add-Type -AssemblyName System.Windows.Forms
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.ShowNewFolderButton = $true
    
    if ($folderBrowser.ShowDialog() -eq 'OK') {
        return $folderBrowser.SelectedPath
    } else {
        Write-Host "No folder selected. Exiting..."
        exit
    }
}

# Function to check if required tools are installed
function Test-RequiredTools {
    $mediaInfoInstalled = $null -ne (Get-Command "mediainfo.exe" -ErrorAction SilentlyContinue)
    $ffprobeInstalled = $null -ne (Get-Command "ffprobe.exe" -ErrorAction SilentlyContinue)
    
    if (-not $mediaInfoInstalled) {
        Write-Host "MediaInfo is not installed or not in PATH. Please install MediaInfo CLI." -ForegroundColor Red
        return $false
    }
    
    if (-not $ffprobeInstalled) {
        Write-Host "FFprobe is not installed or not in PATH. Please install FFmpeg tools." -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Function to extract IMDB ID from filename
function Get-ImdbIdFromFilename {
    param (
        [string]$filename
    )
    
    if ($filename -match "\[imdb-(?<imdbid>tt\d+)\]") {
        return $matches.imdbid
    }
    return $null
}

# Function to get movie info from OMDB API (requires API key)
function Get-MovieInfoFromImdb {
    param (
        [string]$imdbId
    )
    
    # You need to get an API key from http://www.omdbapi.com/
    # Free accounts allow 1,000 requests per day
    $apiKey = "YOUR_OMDB_API_KEY"
    
    # Skip API call if no key is provided or set to placeholder
    if ($apiKey -eq "YOUR_OMDB_API_KEY") {
        Write-Host "  No OMDB API key provided. Skipping online information lookup." -ForegroundColor Yellow
        return $null
    }
    
    try {
        $url = "http://www.omdbapi.com/?i=$imdbId&apikey=$apiKey"
        $response = Invoke-RestMethod -Uri $url -Method Get
        
        if ($response.Response -eq "True") {
            return @{
                Title = $response.Title
                Year = $response.Year
                Runtime = $response.Runtime -replace ' min', ''
                Poster = $response.Poster
                Plot = $response.Plot
                ImdbRating = $response.imdbRating
            }
        }
    } catch {
        Write-Host "  Failed to retrieve movie info for IMDB ID: $imdbId" -ForegroundColor Yellow
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    return $null
}

# Function to get media information using MediaInfo
function Get-MediaInfoDetails {
    param (
        [string]$filePath
    )
    
    try {
        # Get general info
        $generalInfo = mediainfo.exe "--Output=JSON" "$filePath" | ConvertFrom-Json
        $generalTrack = $generalInfo.media.track | Where-Object { $_.'@type' -eq 'General' }
        $videoTrack = $generalInfo.media.track | Where-Object { $_.'@type' -eq 'Video' }
        $audioTrack = $generalInfo.media.track | Where-Object { $_.'@type' -eq 'Audio' }
        
        # Get video codec
        $videoCodec = $videoTrack.Format
        if ($videoTrack.Format_Profile) {
            $videoCodec += " (" + $videoTrack.Format_Profile + ")"
        }
        
        # Get HDR information
        $hdrType = "SDR"
        if ($videoTrack.HDR_Format) {
            $hdrType = $videoTrack.HDR_Format
            if ($videoTrack.HDR_Format_Compatibility) {
                $hdrType += "/" + $videoTrack.HDR_Format_Compatibility
            }
        } elseif ($videoTrack.colour_primaries -match 'BT.2020' -or $videoTrack.transfer_characteristics -match 'PQ|HLG') {
            $hdrType = "HDR"
        }
        
        # Get duration
        $duration = [math]::Round([decimal]$generalTrack.Duration)
        
        # Get audio codec
        $audioCodec = $audioTrack.Format
        if ($audioTrack.Format_Profile) {
            $audioCodec += " (" + $audioTrack.Format_Profile + ")"
        }
        if ($audioTrack.Channels) {
            $audioCodec += " " + $audioTrack.Channels + "ch"
        }
        
        return @{
            Duration = $duration
            VideoCodec = $videoCodec
            AudioCodec = $audioCodec
            HdrType = $hdrType
        }
    } catch {
        Write-Host "Error getting MediaInfo details for $filePath" -ForegroundColor Red
        Write-Host $_.Exception.Message
        return $null
    }
}

# Function to double-check duration with FFprobe
function Get-FFprobeDuration {
    param (
        [string]$filePath
    )
    
    try {
        $ffprobeOutput = ffprobe.exe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$filePath" 2>&1
        if ($ffprobeOutput -match "^\d+\.\d+$") {
            return [math]::Round([decimal]$ffprobeOutput)
        }
    } catch {
        Write-Host "Error getting FFprobe duration for $filePath" -ForegroundColor Red
    }
    
    return $null
}

# Function to create the HTML dashboard
function Create-HtmlDashboard {
    param (
        [array]$movieData,
        [string]$outputPath
    )
    
    # Calculate statistics
    $totalMovies = $movieData.Count
    $suspiciousMovies = ($movieData | Where-Object { $_.IsComplete -eq $false }).Count
    $goodMovies = $totalMovies - $suspiciousMovies
    
    # Prepare data for charts
    $videoCodecStats = $movieData | Group-Object -Property VideoCodec | 
                       Select-Object @{Name='Codec';Expression={$_.Name}}, @{Name='Count';Expression={$_.Count}}
    
    $audioCodecStats = $movieData | Group-Object -Property AudioCodec | 
                       Select-Object @{Name='Codec';Expression={$_.Name}}, @{Name='Count';Expression={$_.Count}}
    
    $hdrTypeStats = $movieData | Group-Object -Property HdrType | 
                    Select-Object @{Name='Type';Expression={$_.Name}}, @{Name='Count';Expression={$_.Count}}
    
    # Size ranges
    $sizeRanges = @(
        @{Range = "< 1 GB"; Min = 0; Max = 1},
        @{Range = "1-2 GB"; Min = 1; Max = 2},
        @{Range = "2-5 GB"; Min = 2; Max = 5},
        @{Range = "5-10 GB"; Min = 5; Max = 10},
        @{Range = "> 10 GB"; Min = 10; Max = [double]::MaxValue}
    )
    
    $sizeStats = @()
    foreach ($range in $sizeRanges) {
        $count = ($movieData | Where-Object { 
            $_.FileSizeGB -ge $range.Min -and $_.FileSizeGB -lt $range.Max 
        }).Count
        $sizeStats += [PSCustomObject]@{
            Range = $range.Range
            Count = $count
        }
    }
    
    # Create HTML content
    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Collection Analysis</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.1/chart.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/js/jquery.dataTables.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/js/dataTables.bootstrap5.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            padding-top: 20px;
        }
        .dashboard-header {
            background-color: #343a40;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .chart-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            height: 300px;
        }
        .stats-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-card h3 {
            margin-bottom: 10px;
            font-size: 18px;
        }
        .stats-card .value {
            font-size: 24px;
            font-weight: bold;
        }
        .table-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .movie-poster {
            width: 60px;
            height: 90px;
            object-fit: cover;
            border-radius: 4px;
        }
        .progress-good {
            background-color: #198754;
        }
        .progress-bad {
            background-color: #dc3545;
        }
        .nav-tabs .nav-link {
            color: #495057;
        }
        .nav-tabs .nav-link.active {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="dashboard-header">
            <div class="row">
                <div class="col-md-8">
                    <h1>Media Collection Analysis</h1>
                    <p>Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
                </div>
                <div class="col-md-4 text-end">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-light" onclick="window.print()">
                            <i class="bi bi-printer"></i> Print Report
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>Total Movies</h3>
                    <div class="value">$totalMovies</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>Complete Movies</h3>
                    <div class="value text-success">$goodMovies</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>Suspicious Movies</h3>
                    <div class="value text-danger">$suspiciousMovies</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h3>Completion Rate</h3>
                    <div class="value">$(if ($totalMovies -gt 0) { [math]::Round(($goodMovies / $totalMovies) * 100) } else { 0 })%</div>
                    <div class="progress mt-2">
                        <div class="progress-bar progress-good" role="progressbar" 
                             style="width: $(if ($totalMovies -gt 0) { ($goodMovies / $totalMovies) * 100 } else { 0 })%" 
                             aria-valuenow="$(if ($totalMovies -gt 0) { ($goodMovies / $totalMovies) * 100 } else { 0 })" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                        <div class="progress-bar progress-bad" role="progressbar" 
                             style="width: $(if ($totalMovies -gt 0) { ($suspiciousMovies / $totalMovies) * 100 } else { 0 })%" 
                             aria-valuenow="$(if ($totalMovies -gt 0) { ($suspiciousMovies / $totalMovies) * 100 } else { 0 })" 
                             aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <canvas id="videoCodecChart"></canvas>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <canvas id="audioCodecChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <canvas id="hdrTypeChart"></canvas>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <canvas id="fileSizeChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="table-card">
            <ul class="nav nav-tabs" id="movieTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="all-tab" data-bs-toggle="tab" data-bs-target="#all" 
                            type="button" role="tab" aria-controls="all" aria-selected="true">
                        All Movies ($totalMovies)
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="suspicious-tab" data-bs-toggle="tab" data-bs-target="#suspicious" 
                            type="button" role="tab" aria-controls="suspicious" aria-selected="false">
                        Suspicious Files ($suspiciousMovies)
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="complete-tab" data-bs-toggle="tab" data-bs-target="#complete" 
                            type="button" role="tab" aria-controls="complete" aria-selected="false">
                        Complete Files ($goodMovies)
                    </button>
                </li>
            </ul>
            <div class="tab-content pt-3" id="movieTabsContent">
                <div class="tab-pane fade show active" id="all" role="tabpanel" aria-labelledby="all-tab">
                    <table id="allMoviesTable" class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Poster</th>
                                <th>Title</th>
                                <th>File Size</th>
                                <th>Duration</th>
                                <th>Expected</th>
                                <th>Video Codec</th>
                                <th>Audio Codec</th>
                                <th>HDR Type</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
"@

    # Add movie rows
    foreach ($movie in $movieData) {
        $statusClass = if ($movie.IsComplete) { "text-success" } else { "text-danger" }
        $statusText = if ($movie.IsComplete) { "Complete" } else { "Incomplete" }
        $posterUrl = if ($movie.PosterUrl -and $movie.PosterUrl -ne "N/A") { $movie.PosterUrl } else { "https://via.placeholder.com/60x90?text=No+Poster" }
        
        $html += @"
                            <tr>
                                <td><img src="$posterUrl" class="movie-poster" alt="$($movie.Title) poster"></td>
                                <td>$($movie.Title) ($($movie.Year))</td>
                                <td>$([math]::Round($movie.FileSizeGB, 2)) GB</td>
                                <td>$($movie.Duration) min</td>
                                <td>$($movie.ExpectedDuration) min</td>
                                <td>$($movie.VideoCodec)</td>
                                <td>$($movie.AudioCodec)</td>
                                <td>$($movie.HdrType)</td>
                                <td class="$statusClass">$statusText</td>
                            </tr>
"@
    }
    
    $html += @"
                        </tbody>
                    </table>
                </div>
                
                <div class="tab-pane fade" id="suspicious" role="tabpanel" aria-labelledby="suspicious-tab">
                    <table id="suspiciousMoviesTable" class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Poster</th>
                                <th>Title</th>
                                <th>File Size</th>
                                <th>Duration</th>
                                <th>Expected</th>
                                <th>Video Codec</th>
                                <th>Audio Codec</th>
                                <th>HDR Type</th>
                                <th>Difference</th>
                            </tr>
                        </thead>
                        <tbody>
"@

    # Add suspicious movie rows
    foreach ($movie in ($movieData | Where-Object { $_.IsComplete -eq $false })) {
        $durationDifference = $movie.ExpectedDuration - $movie.Duration
        $posterUrl = if ($movie.PosterUrl -and $movie.PosterUrl -ne "N/A") { $movie.PosterUrl } else { "https://via.placeholder.com/60x90?text=No+Poster" }
        
        $html += @"
                            <tr>
                                <td><img src="$posterUrl" class="movie-poster" alt="$($movie.Title) poster"></td>
                                <td>$($movie.Title) ($($movie.Year))</td>
                                <td>$([math]::Round($movie.FileSizeGB, 2)) GB</td>
                                <td>$($movie.Duration) min</td>
                                <td>$($movie.ExpectedDuration) min</td>
                                <td>$($movie.VideoCodec)</td>
                                <td>$($movie.AudioCodec)</td>
                                <td>$($movie.HdrType)</td>
                                <td class="text-danger">Missing $durationDifference min</td>
                            </tr>
"@
    }
    
    $html += @"
                        </tbody>
                    </table>
                </div>
                
                <div class="tab-pane fade" id="complete" role="tabpanel" aria-labelledby="complete-tab">
                    <table id="completeMoviesTable" class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Poster</th>
                                <th>Title</th>
                                <th>File Size</th>
                                <th>Duration</th>
                                <th>Expected</th>
                                <th>Video Codec</th>
                                <th>Audio Codec</th>
                                <th>HDR Type</th>
                            </tr>
                        </thead>
                        <tbody>
"@

    # Add complete movie rows
    foreach ($movie in ($movieData | Where-Object { $_.IsComplete -eq $true })) {
        $posterUrl = if ($movie.PosterUrl -and $movie.PosterUrl -ne "N/A") { $movie.PosterUrl } else { "https://via.placeholder.com/60x90?text=No+Poster" }
        
        $html += @"
                            <tr>
                                <td><img src="$posterUrl" class="movie-poster" alt="$($movie.Title) poster"></td>
                                <td>$($movie.Title) ($($movie.Year))</td>
                                <td>$([math]::Round($movie.FileSizeGB, 2)) GB</td>
                                <td>$($movie.Duration) min</td>
                                <td>$($movie.ExpectedDuration) min</td>
                                <td>$($movie.VideoCodec)</td>
                                <td>$($movie.AudioCodec)</td>
                                <td>$($movie.HdrType)</td>
                            </tr>
"@
    }
    
    $html += @"
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize DataTables
        $(document).ready(function() {
            $('#allMoviesTable').DataTable({
                order: [[8, 'asc']], // Sort by status
                pageLength: 25
            });
            
            $('#suspiciousMoviesTable').DataTable({
                order: [[8, 'desc']], // Sort by difference
                pageLength: 25
            });
            
            $('#completeMoviesTable').DataTable({
                pageLength: 25
            });
            
            // Create charts
            // Video Codec Chart
            const videoCodecChart = new Chart(
                document.getElementById('videoCodecChart').getContext('2d'),
                {
                    type: 'pie',
                    data: {
                        labels: [$(($videoCodecStats | ForEach-Object { "'$($_.Codec)'" }) -join ', ')],
                        datasets: [{
                            data: [$(($videoCodecStats | ForEach-Object { $_.Count }) -join ', ')],
                            backgroundColor: [
                                '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                                '#6f42c1', '#5a5c69', '#858796', '#f8f9fc', '#d1d3e2'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                            },
                            title: {
                                display: true,
                                text: 'Video Codecs Distribution'
                            }
                        }
                    }
                }
            );
            
            // Audio Codec Chart
            const audioCodecChart = new Chart(
                document.getElementById('audioCodecChart').getContext('2d'),
                {
                    type: 'pie',
                    data: {
                        labels: [$(($audioCodecStats | ForEach-Object { "'$($_.Codec)'" }) -join ', ')],
                        datasets: [{
                            data: [$(($audioCodecStats | ForEach-Object { $_.Count }) -join ', ')],
                            backgroundColor: [
                                '#1cc88a', '#4e73df', '#36b9cc', '#f6c23e', '#e74a3b',
                                '#6f42c1', '#5a5c69', '#858796', '#f8f9fc', '#d1d3e2'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                            },
                            title: {
                                display: true,
                                text: 'Audio Codecs Distribution'
                            }
                        }
                    }
                }
            );
            
            // HDR Type Chart
            const hdrTypeChart = new Chart(
                document.getElementById('hdrTypeChart').getContext('2d'),
                {
                    type: 'pie',
                    data: {
                        labels: [$(($hdrTypeStats | ForEach-Object { "'$($_.Type)'" }) -join ', ')],
                        datasets: [{
                            data: [$(($hdrTypeStats | ForEach-Object { $_.Count }) -join ', ')],
                            backgroundColor: [
                                '#36b9cc', '#4e73df', '#1cc88a', '#f6c23e', '#e74a3b',
                                '#6f42c1', '#5a5c69', '#858796', '#f8f9fc', '#d1d3e2'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                            },
                            title: {
                                display: true,
                                text: 'HDR Type Distribution'
                            }
                        }
                    }
                }
            );
            
            // File Size Chart
            const fileSizeChart = new Chart(
                document.getElementById('fileSizeChart').getContext('2d'),
                {
                    type: 'bar',
                    data: {
                        labels: [$(($sizeStats | ForEach-Object { "'$($_.Range)'" }) -join ', ')],
                        datasets: [{
                            label: 'Number of Movies',
                            data: [$(($sizeStats | ForEach-Object { $_.Count }) -join ', ')],
                            backgroundColor: '#4e73df'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'File Size Distribution'
                            }
                        }
                    }
                }
            );
        });
    </script>
</body>
</html>
"@

    # Write the HTML file
    $html | Out-File -FilePath $outputPath -Encoding utf8
    
    Write-Host "Dashboard created at: $outputPath" -ForegroundColor Green
    
    # Open the HTML file in the default browser
    Start-Process $outputPath
}

# Main script execution

# Clear screen and show welcome message
Clear-Host
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "           MEDIA COLLECTION ANALYZER                " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
if (-not (Test-RequiredTools)) {
    Write-Host "Please install the required tools and try again." -ForegroundColor Red
    exit
}

# Ask for analysis type
$scanSubfolders = $false
$choice = Read-Host "Do you want to scan subfolders? (Y/N)"
if ($choice -eq "Y" -or $choice -eq "y") {
    $scanSubfolders = $true
}

# Select folder to analyze
Write-Host "Please select the folder containing your media files..." -ForegroundColor Yellow
$folderPath = Show-FolderBrowserDialog -Description "Select a folder containing your media files"
Write-Host "Selected folder: $folderPath" -ForegroundColor Green

# Select output folder
Write-Host "Please select where to save analysis results..." -ForegroundColor Yellow
$outputFolder = Show-FolderBrowserDialog -Description "Select a folder to save analysis results"
Write-Host "Results will be saved to: $outputFolder" -ForegroundColor Green

# Create output subfolder with timestamp
$outputSubfolder = Join-Path $outputFolder "MediaAnalysis_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if (-not (Test-Path $outputSubfolder)) {
    New-Item -Path $outputSubfolder -ItemType Directory | Out-Null
}
Write-Host "Created output folder: $outputSubfolder" -ForegroundColor Green

# Define supported video extensions
$supportedExtensions = @(".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v")

# Get all media files
Write-Host "Scanning for media files..." -ForegroundColor Yellow
$mediaFiles = if ($scanSubfolders) {
    Get-ChildItem -Path $folderPath -Recurse -File | Where-Object { $supportedExtensions -contains $_.Extension }
} else {
    Get-ChildItem -Path $folderPath -File | Where-Object { $supportedExtensions -contains $_.Extension }
}

$totalFiles = $mediaFiles.Count
Write-Host "Found $totalFiles media files to analyze." -ForegroundColor Green

# Create database path
$dbFilePath = Join-Path $outputSubfolder "media_analysis.db"
$htmlPath = Join-Path $outputSubfolder "dashboard.html"

# Initialize array to store movie data
$movieData = @()

# Process each media file
$counter = 0
foreach ($file in $mediaFiles) {
    $counter++
    $percentComplete = [math]::Round(($counter / $totalFiles) * 100, 2)
    
    Write-Progress -Activity "Analyzing Media Files" -Status "$counter of $totalFiles ($percentComplete%)" `
                   -CurrentOperation "Processing $($file.Name)" -PercentComplete $percentComplete
    
    # Get basic file info
    $fileSize = $file.Length / 1GB
    
    # Extract IMDB ID
    $imdbId = Get-ImdbIdFromFilename -filename $file.Name
    
    # Initialize movie info
    $movieInfo = @{
        Filename = $file.Name
        FilePath = $file.FullName
        FileSizeGB = $fileSize
        ImdbId = $imdbId
        Title = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        Year = if ($file.Name -match "\((\d{4})\)") { $matches[1] } else { "Unknown" }
        PosterUrl = "https://via.placeholder.com/60x90?text=No+Poster"
        ExpectedDuration = 0
        Duration = 0
        VideoCodec = "Unknown"
        AudioCodec = "Unknown"
        HdrType = "Unknown"
        IsComplete = $true
    }
    
    # Get IMDB info if available
    if ($imdbId) {
        $omdbInfo = Get-MovieInfoFromImdb -imdbId $imdbId
        if ($omdbInfo) {
            $movieInfo.Title = $omdbInfo.Title
            $movieInfo.Year = $omdbInfo.Year
            $movieInfo.PosterUrl = $omdbInfo.Poster
            $movieInfo.ExpectedDuration = [int]$omdbInfo.Runtime
        }
    }
    
    # Get media info
    Write-Host "  Analyzing $($file.Name)..." -ForegroundColor Cyan
    $mediaInfo = Get-MediaInfoDetails -filePath $file.FullName
    if ($mediaInfo) {
        $movieInfo.Duration = $mediaInfo.Duration / 60  # Convert to minutes
        $movieInfo.VideoCodec = $mediaInfo.VideoCodec
        $movieInfo.AudioCodec = $mediaInfo.AudioCodec
        $movieInfo.HdrType = $mediaInfo.HdrType
    }
    
    # Double-check with FFprobe
    $ffprobeDuration = Get-FFprobeDuration -filePath $file.FullName
    if ($ffprobeDuration) {
        # Use FFprobe duration instead if it's available (convert to minutes)
        $movieInfo.Duration = $ffprobeDuration / 60
    }
    
    # Determine if file is complete
    if ($movieInfo.ExpectedDuration -gt 0) {
        # If we have expected duration from IMDB, use that for comparison
        # Allow for 5% difference (some movies have credits cut off, etc.)
        $durationDifference = $movieInfo.ExpectedDuration - $movieInfo.Duration
        $durationThreshold = $movieInfo.ExpectedDuration * 0.05
        
        if ($durationDifference -gt $durationThreshold) {
            $movieInfo.IsComplete = $false
        }
    }
    
    # Convert movieInfo to PSObject and add to collection
    $movieObject = New-Object PSObject -Property $movieInfo
    $movieData += $movieObject
}

Write-Progress -Activity "Analyzing Media Files" -Completed

# Export data to SQLite database
Write-Host "Creating database..." -ForegroundColor Yellow

# Create SQLite connection using System.Data.SQLite
Add-Type -Path "System.Data.SQLite.dll" -ErrorAction SilentlyContinue

if (-not ([System.AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.FullName -like "*System.Data.SQLite*" })) {
    Write-Host "System.Data.SQLite.dll not found. Using CSV instead." -ForegroundColor Yellow
    
    # Export to CSV as an alternative
    $csvPath = Join-Path $outputFolder "media_analysis.csv"
    $movieData | Export-Csv -Path $csvPath -NoTypeInformation
    Write-Host "Data exported to CSV: $csvPath" -ForegroundColor Green
} else {
    # Create SQLite database
    $connStr = "Data Source=$dbFilePath;Version=3;"
    $conn = New-Object System.Data.SQLite.SQLiteConnection($connStr)
    $conn.Open()
    
    # Create table
    $createTableCmd = $conn.CreateCommand()
    $createTableCmd.CommandText = @"
CREATE TABLE IF NOT EXISTS Movies (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Filename TEXT,
    FilePath TEXT,
    FileSizeGB REAL,
    ImdbId TEXT,
    Title TEXT,
    Year TEXT,
    PosterUrl TEXT,
    ExpectedDuration INTEGER,
    Duration INTEGER,
    VideoCodec TEXT,
    AudioCodec TEXT,
    HdrType TEXT,
    IsComplete INTEGER
);
"@
    $createTableCmd.ExecuteNonQuery() | Out-Null
    
    # Insert data
    $insertCmd = $conn.CreateCommand()
    $insertCmd.CommandText = @"
INSERT INTO Movies (
    Filename, FilePath, FileSizeGB, ImdbId, Title, Year, PosterUrl,
    ExpectedDuration, Duration, VideoCodec, AudioCodec, HdrType, IsComplete
) VALUES (
    @Filename, @FilePath, @FileSizeGB, @ImdbId, @Title, @Year, @PosterUrl,
    @ExpectedDuration, @Duration, @VideoCodec, @AudioCodec, @HdrType, @IsComplete
);
"@
    
    $insertCmd.Parameters.Add("@Filename", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@FilePath", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@FileSizeGB", [System.Data.DbType]::Double) | Out-Null
    $insertCmd.Parameters.Add("@ImdbId", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@Title", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@Year", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@PosterUrl", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@ExpectedDuration", [System.Data.DbType]::Int32) | Out-Null
    $insertCmd.Parameters.Add("@Duration", [System.Data.DbType]::Int32) | Out-Null
    $insertCmd.Parameters.Add("@VideoCodec", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@AudioCodec", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@HdrType", [System.Data.DbType]::String) | Out-Null
    $insertCmd.Parameters.Add("@IsComplete", [System.Data.DbType]::Int32) | Out-Null
    
    foreach ($movie in $movieData) {
        $insertCmd.Parameters["@Filename"].Value = $movie.Filename
        $insertCmd.Parameters["@FilePath"].Value = $movie.FilePath
        $insertCmd.Parameters["@FileSizeGB"].Value = $movie.FileSizeGB
        $insertCmd.Parameters["@ImdbId"].Value = $movie.ImdbId
        $insertCmd.Parameters["@Title"].Value = $movie.Title
        $insertCmd.Parameters["@Year"].Value = $movie.Year
        $insertCmd.Parameters["@PosterUrl"].Value = $movie.PosterUrl
        $insertCmd.Parameters["@ExpectedDuration"].Value = [int]$movie.ExpectedDuration
        $insertCmd.Parameters["@Duration"].Value = [int]$movie.Duration
        $insertCmd.Parameters["@VideoCodec"].Value = $movie.VideoCodec
        $insertCmd.Parameters["@AudioCodec"].Value = $movie.AudioCodec
        $insertCmd.Parameters["@HdrType"].Value = $movie.HdrType
        $insertCmd.Parameters["@IsComplete"].Value = [int]$movie.IsComplete
        
        $insertCmd.ExecuteNonQuery() | Out-Null
    }
    
    # Close connection
    $conn.Close()
    Write-Host "Database created: $dbFilePath" -ForegroundColor Green
}

# Create HTML dashboard
Write-Host "Creating HTML dashboard..." -ForegroundColor Yellow
Create-HtmlDashboard -movieData $movieData -outputPath $htmlPath

# Summary
$suspiciousMovies = ($movieData | Where-Object { $_.IsComplete -eq $false }).Count
$goodMovies = $movieData.Count - $suspiciousMovies

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "                 ANALYSIS COMPLETE                  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Total Movies: $($movieData.Count)" -ForegroundColor White
Write-Host "Complete Movies: $goodMovies" -ForegroundColor Green
Write-Host "Suspicious Movies: $suspiciousMovies" -ForegroundColor Red
Write-Host ""
Write-Host "Results saved to: $outputSubfolder" -ForegroundColor Yellow
Write-Host "Dashboard opened in your browser." -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

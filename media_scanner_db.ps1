# Media Collection Scanner - SQLite DB Version
# This script analyzes media files and saves the data to a SQLite database for later reporting

# Function to download SQLite binaries if needed
function Initialize-SQLiteEnvironment {
    $targetDir = "C:\MediaAnalyzer\Tools"
    $sqlitePath = Join-Path -Path $targetDir -ChildPath "sqlite3.exe"
    
    # Create directory if it doesn't exist
    if (-not (Test-Path $targetDir)) {
        New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
    }
    
    # Download SQLite if not available
    if (-not (Test-Path $sqlitePath)) {
        Write-Host "SQLite not found. Downloading SQLite..." -ForegroundColor Yellow
        $sqliteUrl = "https://www.sqlite.org/2023/sqlite-tools-win32-x86-3420000.zip"
        $tempZipPath = Join-Path -Path $env:TEMP -ChildPath "sqlite_temp.zip"
        
        try {
            Invoke-WebRequest -Uri $sqliteUrl -OutFile $tempZipPath
            
            # Extract SQLite
            $extractPath = Join-Path -Path $env:TEMP -ChildPath "sqlite_extract"
            if (Test-Path $extractPath) { Remove-Item -Path $extractPath -Recurse -Force }
            New-Item -Path $extractPath -ItemType Directory -Force | Out-Null
            
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory($tempZipPath, $extractPath)
            
            # Find sqlite3.exe in extraction folder (might be in a subfolder)
            $sqliteExe = Get-ChildItem -Path $extractPath -Filter "sqlite3.exe" -Recurse | Select-Object -First 1
            if ($sqliteExe) {
                Copy-Item -Path $sqliteExe.FullName -Destination $sqlitePath -Force
                Write-Host "SQLite downloaded and installed successfully." -ForegroundColor Green
            } else {
                Write-Host "Failed to find sqlite3.exe in the downloaded package." -ForegroundColor Red
                return $false
            }
            
            # Clean up
            Remove-Item -Path $tempZipPath -Force
            Remove-Item -Path $extractPath -Recurse -Force
        } catch {
            Write-Host "Failed to download SQLite: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    
    # Install System.Data.SQLite module if needed
    if (-not (Get-Module -ListAvailable -Name PSSQLite)) {
        Write-Host "Installing PSSQLite module..." -ForegroundColor Yellow
        try {
            Install-Module -Name PSSQLite -Force -Scope CurrentUser
            Write-Host "PSSQLite module installed successfully." -ForegroundColor Green
        } catch {
            Write-Host "Failed to install PSSQLite module: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
    
    # Import module
    Import-Module PSSQLite
    
    return $true
}

# Function to initialize the database
function Initialize-Database {
    param (
        [string]$dbPath
    )
    
    try {
        # Create the database file if it doesn't exist
        if (-not (Test-Path $dbPath)) {
            New-Item -Path (Split-Path -Path $dbPath -Parent) -ItemType Directory -Force | Out-Null
            $null = New-Item -Path $dbPath -ItemType File -Force
        }
        
        # Create tables if they don't exist
        $query = @"
CREATE TABLE IF NOT EXISTS Folders (
    FolderId INTEGER PRIMARY KEY AUTOINCREMENT,
    FolderPath TEXT NOT NULL UNIQUE,
    LastScanned TEXT,
    ScanInProgress INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS MediaFiles (
    FileId INTEGER PRIMARY KEY AUTOINCREMENT,
    FolderId INTEGER,
    Filename TEXT NOT NULL,
    FilePath TEXT NOT NULL UNIQUE,
    LastModified TEXT,
    FileSizeGB REAL,
    ImdbId TEXT,
    Title TEXT,
    Year TEXT,
    PosterUrl TEXT,
    ExpectedDuration INTEGER,
    Duration REAL,
    VideoCodec TEXT,
    AudioCodec TEXT,
    HdrType TEXT,
    IsComplete INTEGER,
    ManuallyApproved INTEGER,
    DateAdded TEXT,
    FOREIGN KEY (FolderId) REFERENCES Folders(FolderId)
);

CREATE TABLE IF NOT EXISTS ApiKeyStatus (
    ApiKey TEXT PRIMARY KEY,
    LastFailedTime TEXT
);

CREATE INDEX IF NOT EXISTS idx_MediaFiles_FilePath ON MediaFiles(FilePath);
CREATE INDEX IF NOT EXISTS idx_MediaFiles_ImdbId ON MediaFiles(ImdbId);
CREATE INDEX IF NOT EXISTS idx_MediaFiles_IsComplete ON MediaFiles(IsComplete);
"@
        
        Invoke-SqliteQuery -DataSource $dbPath -Query $query
        
        return $true
    } catch {
        Write-Host "Error initializing database: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

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

# Function to integrate with existing Get-ImdbIdFromFilename function
function Get-ImdbIdFromFilename {
    param (
        [string]$filename
    )
    
    # Try to match standard [imdb-ttXXXXXXX] format
    if ($filename -match "\[imdb-(?<imdbid>tt\d+)\]") {
        return $matches.imdbid
    }
    
    # Try to match alternative {imdb-ttXXXXXXX} format
    if ($filename -match "\{imdb-(?<imdbid>tt\d+)\}") {
        return $matches.imdbid
    }
    
    # Try to match just ttXXXXXXX anywhere in the filename
    if ($filename -match "(?<imdbid>tt\d{7,8})") {
        return $matches.imdbid
    }
    
    return $null
}

# Function to get movie info from OMDB API with multiple API key support and 24h cooldown
function Get-MovieInfoFromImdb {
    param (
        [string]$imdbId,
        [string]$dbPath
    )
    
    # Multiple API keys - add your keys here
    $apiKeys = @(
        "42cea86b",
        "382cfaed",
        "71efd438",
        "5b1bbbfa",
        "ec8397b2"
    )
    
    # Filter out placeholder keys
    $validApiKeys = $apiKeys | Where-Object { $_ -ne "YOUR_OMDB_API_KEY_1" -and $_ -ne "YOUR_OMDB_API_KEY_2" -and $_ -ne "YOUR_OMDB_API_KEY_3" -and $_ -ne "YOUR_OMDB_API_KEY_4" -and $_ -ne "YOUR_OMDB_API_KEY_5" }
    
    if ($validApiKeys.Count -eq 0) {
        Write-Host "  No valid OMDB API keys provided. Skipping online information lookup." -ForegroundColor Yellow
        return $null
    }

    # Keep track of which keys we've tried in this function call
    $triedKeys = @{}
    
    # Get API key status from the database
    $keyStatus = @{}
    $query = "SELECT ApiKey, LastFailedTime FROM ApiKeyStatus"
    $apiKeyStatusResults = Invoke-SqliteQuery -DataSource $dbPath -Query $query
    
    foreach ($result in $apiKeyStatusResults) {
        $keyStatus[$result.ApiKey] = $result.LastFailedTime
    }
    
    # Flag to track if we need to update the database
    $databaseNeedsUpdate = $false
    $keysToUpdate = @()
    $keysToRemove = @()
    
    # Process each valid API key
    foreach ($apiKey in $validApiKeys) {
        # Skip if we've already tried this key in this function call
        if ($triedKeys.ContainsKey($apiKey)) {
            continue
        }
        
        # Mark this key as tried
        $triedKeys[$apiKey] = $true
        
        # Check if this key is in cooldown
        if ($keyStatus.ContainsKey($apiKey)) {
            $lastFailedTime = [datetime]::Parse($keyStatus[$apiKey])
            $timeSinceFailed = (Get-Date) - $lastFailedTime
            
            # Skip this key if it failed within the last 24 hours
            if ($timeSinceFailed.TotalHours -lt 24) {
                Write-Host "  Skipping API key in cooldown (failed $([Math]::Round($timeSinceFailed.TotalHours, 1)) hours ago)" -ForegroundColor Yellow
                continue
            } else {
                # Key is out of cooldown, remove it from status
                $keysToRemove += $apiKey
                $databaseNeedsUpdate = $true
            }
        }
        
        try {
            $url = "http://www.omdbapi.com/?i=$imdbId&apikey=$apiKey"
            $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
            
            if ($response.Response -eq "True") {
                # On success, remove this key from the failed status if it exists
                if ($keyStatus.ContainsKey($apiKey)) {
                    $keysToRemove += $apiKey
                    $databaseNeedsUpdate = $true
                }
                
                # Update database if needed
                if ($databaseNeedsUpdate) {
                    # Remove keys that are out of cooldown
                    foreach ($key in $keysToRemove) {
                        $removeQuery = "DELETE FROM ApiKeyStatus WHERE ApiKey = @ApiKey"
                        Invoke-SqliteQuery -DataSource $dbPath -Query $removeQuery -SqlParameters @{
                            ApiKey = $key
                        }
                    }
                    
                    # Add keys that are in cooldown
                    foreach ($keyToUpdate in $keysToUpdate) {
                        $insertQuery = "INSERT OR REPLACE INTO ApiKeyStatus (ApiKey, LastFailedTime) VALUES (@ApiKey, @LastFailedTime)"
                        Invoke-SqliteQuery -DataSource $dbPath -Query $insertQuery -SqlParameters @{
                            ApiKey = $keyToUpdate.Key
                            LastFailedTime = $keyToUpdate.Value
                        }
                    }
                }
                
                return @{
                    Title = $response.Title
                    Year = $response.Year
                    Runtime = $response.Runtime -replace ' min', ''
                    Poster = $response.Poster
                    Plot = $response.Plot
                    ImdbRating = $response.imdbRating
                }
            } elseif ($response.Error -eq "Invalid API key!" -or $response.Error -eq "Request limit reached!") {
                # API key invalid or daily limit reached, mark as failed
                $failedTime = (Get-Date).ToString("o")
                $keysToUpdate += @{ Key = $apiKey; Value = $failedTime }
                $databaseNeedsUpdate = $true
                
                Write-Host "  API key '$apiKey' limit reached. Marked for 24h cooldown, trying next key." -ForegroundColor Yellow
            }
        } catch {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 401) {
                # Unauthorized - API key issue, mark as failed
                $failedTime = (Get-Date).ToString("o")
                $keysToUpdate += @{ Key = $apiKey; Value = $failedTime }
                $databaseNeedsUpdate = $true
                
                Write-Host "  API key '$apiKey' unauthorized. Marked for 24h cooldown, trying next key." -ForegroundColor Yellow
            } else {
                # Other network/server error, log but don't mark the key as failed
                Write-Host "  Network error with API key '$apiKey': $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    # Update database if needed (only at the end, not for each key)
    if ($databaseNeedsUpdate) {
        # Remove keys that are out of cooldown
        foreach ($key in $keysToRemove) {
            $removeQuery = "DELETE FROM ApiKeyStatus WHERE ApiKey = @ApiKey"
            Invoke-SqliteQuery -DataSource $dbPath -Query $removeQuery -SqlParameters @{
                ApiKey = $key
            }
        }
        
        # Add keys that are in cooldown
        foreach ($keyToUpdate in $keysToUpdate) {
            $insertQuery = "INSERT OR REPLACE INTO ApiKeyStatus (ApiKey, LastFailedTime) VALUES (@ApiKey, @LastFailedTime)"
            Invoke-SqliteQuery -DataSource $dbPath -Query $insertQuery -SqlParameters @{
                ApiKey = $keyToUpdate.Key
                LastFailedTime = $keyToUpdate.Value
            }
        }
    }
    
    # If we get here, all keys failed or were in cooldown
    Write-Host "  All API keys failed or in cooldown. Skipping online information lookup." -ForegroundColor Yellow
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

# Function to check if file exists in database
function Test-FileInDatabase {
    param (
        [string]$filePath,
        [string]$dbPath
    )
    
    $query = "SELECT FileId, LastModified, ManuallyApproved FROM MediaFiles WHERE FilePath = @FilePath"
    $result = Invoke-SqliteQuery -DataSource $dbPath -Query $query -SqlParameters @{
        FilePath = $filePath
    }
    
    if ($result) {
        return $result
    } else {
        return $null
    }
}

# Function to register a folder in the database
function Register-FolderInDatabase {
    param (
        [string]$folderPath,
        [string]$dbPath
    )
    
    # Check if folder already exists
    $query = "SELECT FolderId FROM Folders WHERE FolderPath = @FolderPath"
    $result = Invoke-SqliteQuery -DataSource $dbPath -Query $query -SqlParameters @{
        FolderPath = $folderPath
    }
    
    if ($result) {
        # Update scan in progress flag
        $updateQuery = "UPDATE Folders SET ScanInProgress = 1 WHERE FolderId = @FolderId"
        Invoke-SqliteQuery -DataSource $dbPath -Query $updateQuery -SqlParameters @{
            FolderId = $result.FolderId
        }
        return $result.FolderId
    } else {
        # Insert new folder
        $insertQuery = "INSERT INTO Folders (FolderPath, ScanInProgress) VALUES (@FolderPath, 1)"
        Invoke-SqliteQuery -DataSource $dbPath -Query $insertQuery -SqlParameters @{
            FolderPath = $folderPath
        }
        
        # Get the new folder ID
        $getIdQuery = "SELECT FolderId FROM Folders WHERE FolderPath = @FolderPath"
        $newFolder = Invoke-SqliteQuery -DataSource $dbPath -Query $getIdQuery -SqlParameters @{
            FolderPath = $folderPath
        }
        
        return $newFolder.FolderId
    }
}

# Function to mark folder scan as complete
function Complete-FolderScan {
    param (
        [int]$folderId,
        [string]$dbPath
    )
    
    $updateQuery = "UPDATE Folders SET LastScanned = @LastScanned, ScanInProgress = 0 WHERE FolderId = @FolderId"
    Invoke-SqliteQuery -DataSource $dbPath -Query $updateQuery -SqlParameters @{
        FolderId = $folderId
        LastScanned = (Get-Date).ToString("o")
    }
}

# Function to add or update a media file in the database
function Update-MediaFileInDatabase {
    param (
        [hashtable]$fileInfo,
        [string]$dbPath,
        [int]$folderId
    )
    
    # Check if file exists
    $existingFile = Test-FileInDatabase -filePath $fileInfo.FilePath -dbPath $dbPath
    
    if ($existingFile) {
        # Update existing file
        $updateQuery = @"
UPDATE MediaFiles SET 
    Filename = @Filename,
    LastModified = @LastModified,
    FileSizeGB = @FileSizeGB,
    ImdbId = @ImdbId,
    Title = @Title,
    Year = @Year,
    PosterUrl = @PosterUrl,
    ExpectedDuration = @ExpectedDuration,
    Duration = @Duration,
    VideoCodec = @VideoCodec,
    AudioCodec = @AudioCodec,
    HdrType = @HdrType,
    IsComplete = @IsComplete,
    ManuallyApproved = @ManuallyApproved
WHERE FileId = @FileId
"@
        
        Invoke-SqliteQuery -DataSource $dbPath -Query $updateQuery -SqlParameters @{
            FileId = $existingFile.FileId
            Filename = $fileInfo.Filename
            LastModified = $fileInfo.LastModified
            FileSizeGB = $fileInfo.FileSizeGB
            ImdbId = $fileInfo.ImdbId
            Title = $fileInfo.Title
            Year = $fileInfo.Year
            PosterUrl = $fileInfo.PosterUrl
            ExpectedDuration = $fileInfo.ExpectedDuration
            Duration = $fileInfo.Duration
            VideoCodec = $fileInfo.VideoCodec
            AudioCodec = $fileInfo.AudioCodec
            HdrType = $fileInfo.HdrType
            IsComplete = if ($fileInfo.IsComplete) { 1 } else { 0 }
            ManuallyApproved = if ($fileInfo.ManuallyApproved) { 1 } else { 0 }
        }
    } else {
        # Insert new file
        $insertQuery = @"
INSERT INTO MediaFiles (
    FolderId,
    Filename,
    FilePath,
    LastModified,
    FileSizeGB,
    ImdbId,
    Title,
    Year,
    PosterUrl,
    ExpectedDuration,
    Duration,
    VideoCodec,
    AudioCodec,
    HdrType,
    IsComplete,
    ManuallyApproved,
    DateAdded
) VALUES (
    @FolderId,
    @Filename,
    @FilePath,
    @LastModified,
    @FileSizeGB,
    @ImdbId,
    @Title,
    @Year,
    @PosterUrl,
    @ExpectedDuration,
    @Duration,
    @VideoCodec,
    @AudioCodec,
    @HdrType,
    @IsComplete,
    @ManuallyApproved,
    @DateAdded
)
"@
        
        Invoke-SqliteQuery -DataSource $dbPath -Query $insertQuery -SqlParameters @{
            FolderId = $folderId
            Filename = $fileInfo.Filename
            FilePath = $fileInfo.FilePath
            LastModified = $fileInfo.LastModified
            FileSizeGB = $fileInfo.FileSizeGB
            ImdbId = $fileInfo.ImdbId
            Title = $fileInfo.Title
            Year = $fileInfo.Year
            PosterUrl = $fileInfo.PosterUrl
            ExpectedDuration = $fileInfo.ExpectedDuration
            Duration = $fileInfo.Duration
            VideoCodec = $fileInfo.VideoCodec
            AudioCodec = $fileInfo.AudioCodec
            HdrType = $fileInfo.HdrType
            IsComplete = if ($fileInfo.IsComplete) { 1 } else { 0 }
            ManuallyApproved = if ($fileInfo.ManuallyApproved) { 1 } else { 0 }
            DateAdded = (Get-Date).ToString("o")
        }
    }
}

# Function to scan a folder
function Scan-MediaFolder {
    param (
        [string]$folderPath,
        [bool]$scanSubfolders,
        [bool]$skipApproved,
        [string]$dbPath
    )
    
    # Register folder in database
    $folderId = Register-FolderInDatabase -folderPath $folderPath -dbPath $dbPath
    
    # Define supported video extensions
    $supportedExtensions = @(".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v")
    
    # Get all media files
    Write-Host "Scanning for media files in $folderPath..." -ForegroundColor Yellow
    $mediaFiles = if ($scanSubfolders) {
        Get-ChildItem -Path $folderPath -Recurse -File | Where-Object { $supportedExtensions -contains $_.Extension }
    } else {
        Get-ChildItem -Path $folderPath -File | Where-Object { $supportedExtensions -contains $_.Extension }
    }
    
    $totalFiles = $mediaFiles.Count
    Write-Host "Found $totalFiles media files to analyze." -ForegroundColor Green
    
    # Process each media file
    $counter = 0
    $processedCount = 0
    $skippedCount = 0
    
    foreach ($file in $mediaFiles) {
        $counter++
        $percentComplete = [math]::Round(($counter / $totalFiles) * 100, 2)
        
        Write-Progress -Activity "Analyzing Media Files" -Status "$counter of $totalFiles ($percentComplete%)" `
                       -CurrentOperation "Processing $($file.Name)" -PercentComplete $percentComplete
        
        # Check if file is already processed and approved
        $existingFile = Test-FileInDatabase -filePath $file.FullName -dbPath $dbPath
        
        $shouldProcess = $true
        if ($existingFile) {
            # Check if file has been manually approved and we're skipping approved files
            if ($skipApproved -and $existingFile.ManuallyApproved -eq 1) {
                Write-Host "  Skipping approved file: $($file.Name)" -ForegroundColor DarkGray
                $skippedCount++
                $shouldProcess = $false
            }
            # Check if file hasn't been modified since last scan
            elseif ($existingFile.LastModified -eq $file.LastWriteTime.ToString("o")) {
                Write-Host "  Using cached data for: $($file.Name)" -ForegroundColor DarkGray
                $skippedCount++
                $shouldProcess = $false
            }
        }
        
        if ($shouldProcess) {
            # Get basic file info
            $fileSize = $file.Length / 1GB
            
            # Extract IMDB ID
            $imdbId = Get-ImdbIdFromFilename -filename $file.Name
            
            # Initialize movie info
            $movieInfo = @{
                Filename = $file.Name
                FilePath = $file.FullName
                LastModified = $file.LastWriteTime.ToString("o")
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
                ManuallyApproved = if ($existingFile -and $existingFile.ManuallyApproved -eq 1) { $true } else { $false }
            }
            
            # Get IMDB info if available
            if ($imdbId) {
                $omdbInfo = Get-MovieInfoFromImdb -imdbId $imdbId -dbPath $dbPath
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
            if ($movieInfo.ManuallyApproved) {
                # If manually approved, always mark as complete
                $movieInfo.IsComplete = $true
            } elseif ($movieInfo.ExpectedDuration -gt 0) {
                # If we have expected duration from IMDB, use that for comparison
                # Allow for 5% difference (some movies have credits cut off, etc.)
                $durationDifference = $movieInfo.ExpectedDuration - $movieInfo.Duration
                $durationThreshold = $movieInfo.ExpectedDuration * 0.05
                
                if ($durationDifference -gt $durationThreshold) {
                    $movieInfo.IsComplete = $false
                }
            }
            
            # Update database
            Update-MediaFileInDatabase -fileInfo $movieInfo -dbPath $dbPath -folderId $folderId
            $processedCount++
        }
    }
    
    Write-Progress -Activity "Analyzing Media Files" -Completed
    
    # Mark folder scan as complete
    Complete-FolderScan -folderId $folderId -dbPath $dbPath
    
    return @{
        TotalFiles = $totalFiles
        ProcessedCount = $processedCount
        SkippedCount = $skippedCount
    }
}

# Function to get stats for a folder
function Get-FolderStats {
    param (
        [int]$folderId,
        [string]$dbPath
    )
    
    $query = @"
SELECT 
    COUNT(*) AS TotalFiles,
    SUM(CASE WHEN IsComplete = 1 THEN 1 ELSE 0 END) AS CompleteFiles,
    SUM(CASE WHEN IsComplete = 0 THEN 1 ELSE 0 END) AS IncompleteFiles,
    SUM(CASE WHEN ManuallyApproved = 1 THEN 1 ELSE 0 END) AS ApprovedFiles,
    SUM(FileSizeGB) AS TotalSizeGB
FROM MediaFiles
WHERE FolderId = @FolderId
"@
    
    $result = Invoke-SqliteQuery -DataSource $dbPath -Query $query -SqlParameters @{
        FolderId = $folderId
    }
    
    return $result
}

# Function to get total stats from all folders
function Get-TotalStats {
    param (
        [string]$dbPath
    )
    
    $query = @"
SELECT 
    COUNT(*) AS TotalFiles,
    SUM(CASE WHEN IsComplete = 1 THEN 1 ELSE 0 END) AS CompleteFiles,
    SUM(CASE WHEN IsComplete = 0 THEN 1 ELSE 0 END) AS IncompleteFiles,
    SUM(CASE WHEN ManuallyApproved = 1 THEN 1 ELSE 0 END) AS ApprovedFiles,
    SUM(FileSizeGB) AS TotalSizeGB
FROM MediaFiles
"@
    
    $result = Invoke-SqliteQuery -DataSource $dbPath -Query $query
    
    return $result
}

# Function to display folder selection menu
function Show-FolderSelectionMenu {
    param (
        [string]$dbPath
    )
    
    $query = "SELECT FolderId, FolderPath, LastScanned FROM Folders ORDER BY LastScanned DESC"
    $folders = Invoke-SqliteQuery -DataSource $dbPath -Query $query
    
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "             SELECT FOLDER TO SCAN                  " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Get stats for all folders
    $totalStats = Get-TotalStats -dbPath $dbPath
    Write-Host "TOTAL LIBRARY STATISTICS" -ForegroundColor Green
    Write-Host "Total Files: $($totalStats.TotalFiles)" -ForegroundColor White
    Write-Host "Complete Movies: $($totalStats.CompleteFiles)" -ForegroundColor Green
    Write-Host "Suspicious Movies: $($totalStats.IncompleteFiles)" -ForegroundColor Red
    Write-Host "Manually Approved: $($totalStats.ApprovedFiles)" -ForegroundColor Cyan
    Write-Host "Total Size: $([math]::Round($totalStats.TotalSizeGB, 2)) GB" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "REGISTERED FOLDERS:" -ForegroundColor Yellow
    
    if ($folders.Count -eq 0) {
        Write-Host "No folders registered. Please add a new folder." -ForegroundColor Yellow
    } else {
        for ($i = 0; $i -lt $folders.Count; $i++) {
            $folder = $folders[$i]
            $lastScannedString = if ($folder.LastScanned) { 
                "Last scanned: " + [datetime]::Parse($folder.LastScanned).ToString("yyyy-MM-dd HH:mm:ss") 
            } else { 
                "Never scanned" 
            }
            
            # Get stats for this folder
            $stats = Get-FolderStats -folderId $folder.FolderId -dbPath $dbPath
            
            Write-Host "[$($i+1)] $($folder.FolderPath)" -ForegroundColor Cyan
            Write-Host "    $lastScannedString" -ForegroundColor DarkGray
            if ($stats.TotalFiles -gt 0) {
                Write-Host "    Files: $($stats.TotalFiles) | Complete: $($stats.CompleteFiles) | Suspicious: $($stats.IncompleteFiles) | Size: $([math]::Round($stats.TotalSizeGB, 2)) GB" -ForegroundColor DarkGray
            }
        }
    }
    
    Write-Host ""
    Write-Host "[A] Add new folder" -ForegroundColor Green
    Write-Host "[S] Scan all folders" -ForegroundColor Magenta
    Write-Host "[Q] Quit" -ForegroundColor Red
    Write-Host ""
    
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "Q" { return $null }
        "q" { return $null }
        "A" { return "ADD_NEW" }
        "a" { return "ADD_NEW" }
        "S" { return "SCAN_ALL" }
        "s" { return "SCAN_ALL" }
        default {
            $index = [int]$choice - 1
            if ($index -ge 0 -and $index -lt $folders.Count) {
                return $folders[$index].FolderPath
            } else {
                Write-Host "Invalid choice. Press any key to continue..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                return Show-FolderSelectionMenu -dbPath $dbPath
            }
        }
    }
}

# Main script execution

# Clear screen and show welcome message
Clear-Host
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "          MEDIA COLLECTION SCANNER - DB             " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Initialize SQLite environment
if (-not (Initialize-SQLiteEnvironment)) {
    Write-Host "Failed to initialize SQLite environment. Exiting..." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Check for required tools
if (-not (Test-RequiredTools)) {
    Write-Host "Please install the required tools and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Define the path to SQLite database
$dataBaseDir = "C:\MediaAnalyzer"
$dbPath = Join-Path -Path $dataBaseDir -ChildPath "media_library.db"

# Initialize the database
if (-not (Initialize-Database -dbPath $dbPath)) {
    Write-Host "Failed to initialize database. Exiting..." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Main menu loop
while ($true) {
    $folderChoice = Show-FolderSelectionMenu -dbPath $dbPath
    
    if ($null -eq $folderChoice) {
        # Exit the script
        break
    } elseif ($folderChoice -eq "ADD_NEW") {
        # Add new folder
        Write-Host "Please select a folder to add to the media library..." -ForegroundColor Yellow
        $newFolderPath = Show-FolderBrowserDialog -Description "Select a folder containing your media files"
        
        if ($newFolderPath) {
            # Register the folder
            $folderId = Register-FolderInDatabase -folderPath $newFolderPath -dbPath $dbPath
            Complete-FolderScan -folderId $folderId -dbPath $dbPath
            Write-Host "Folder added: $newFolderPath" -ForegroundColor Green
            
            # Ask if user wants to scan it now
            $scanNow = Read-Host "Do you want to scan this folder now? (Y/N)"
            if ($scanNow -eq "Y" -or $scanNow -eq "y") {
                # Scan settings
                $scanSubfolders = $false
                $choice = Read-Host "Do you want to scan subfolders? (Y/N)"
                if ($choice -eq "Y" -or $choice -eq "y") {
                    $scanSubfolders = $true
                }
                
                $skipApproved = $false
                $choice = Read-Host "Do you want to skip previously approved files? (Y/N)"
                if ($choice -eq "Y" -or $choice -eq "y") {
                    $skipApproved = $true
                }
                
                # Scan the folder
                $result = Scan-MediaFolder -folderPath $newFolderPath -scanSubfolders $scanSubfolders -skipApproved $skipApproved -dbPath $dbPath
                
                Write-Host "====================================================" -ForegroundColor Cyan
                Write-Host "                 SCAN COMPLETE                      " -ForegroundColor Cyan
                Write-Host "====================================================" -ForegroundColor Cyan
                Write-Host "Total Files: $($result.TotalFiles)" -ForegroundColor White
                Write-Host "Processed Files: $($result.ProcessedCount)" -ForegroundColor Green
                Write-Host "Skipped Files: $($result.SkippedCount)" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "Press any key to continue..."
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
        }
    } elseif ($folderChoice -eq "SCAN_ALL") {
        # Scan all folders
        $scanSubfolders = $false
        $choice = Read-Host "Do you want to scan subfolders? (Y/N)"
        if ($choice -eq "Y" -or $choice -eq "y") {
            $scanSubfolders = $true
        }
        
        $skipApproved = $false
        $choice = Read-Host "Do you want to skip previously approved files? (Y/N)"
        if ($choice -eq "Y" -or $choice -eq "y") {
            $skipApproved = $true
        }
        
        # Get all folders
        $query = "SELECT FolderId, FolderPath FROM Folders"
        $folders = Invoke-SqliteQuery -DataSource $dbPath -Query $query
        
        $totalProcessed = 0
        $totalSkipped = 0
        $totalFound = 0
        
        foreach ($folder in $folders) {
            Write-Host "====================================================" -ForegroundColor Cyan
            Write-Host "Scanning folder: $($folder.FolderPath)" -ForegroundColor Cyan
            Write-Host "====================================================" -ForegroundColor Cyan
            
            $result = Scan-MediaFolder -folderPath $folder.FolderPath -scanSubfolders $scanSubfolders -skipApproved $skipApproved -dbPath $dbPath
            
            $totalFound += $result.TotalFiles
            $totalProcessed += $result.ProcessedCount
            $totalSkipped += $result.SkippedCount
            
            Write-Host "Files found: $($result.TotalFiles) | Processed: $($result.ProcessedCount) | Skipped: $($result.SkippedCount)" -ForegroundColor Green
            Write-Host ""
        }
        
        Write-Host "====================================================" -ForegroundColor Cyan
        Write-Host "              ALL SCANS COMPLETE                    " -ForegroundColor Cyan
        Write-Host "====================================================" -ForegroundColor Cyan
        Write-Host "Total Files Found: $totalFound" -ForegroundColor White
        Write-Host "Total Files Processed: $totalProcessed" -ForegroundColor Green
        Write-Host "Total Files Skipped: $totalSkipped" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to continue..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } else {
        # Scan individual folder
        $scanSubfolders = $false
        $choice = Read-Host "Do you want to scan subfolders? (Y/N)"
        if ($choice -eq "Y" -or $choice -eq "y") {
            $scanSubfolders = $true
        }
        
        $skipApproved = $false
        $choice = Read-Host "Do you want to skip previously approved files? (Y/N)"
        if ($choice -eq "Y" -or $choice -eq "y") {
            $skipApproved = $true
        }
        
        # Scan the folder
        $result = Scan-MediaFolder -folderPath $folderChoice -scanSubfolders $scanSubfolders -skipApproved $skipApproved -dbPath $dbPath
        
        Write-Host "====================================================" -ForegroundColor Cyan
        Write-Host "                 SCAN COMPLETE                      " -ForegroundColor Cyan
        Write-Host "====================================================" -ForegroundColor Cyan
        Write-Host "Total Files: $($result.TotalFiles)" -ForegroundColor White
        Write-Host "Processed Files: $($result.ProcessedCount)" -ForegroundColor Green
        Write-Host "Skipped Files: $($result.SkippedCount)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to continue..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

Write-Host "Thank you for using Media Collection Scanner!" -ForegroundColor Green
Write-Host "Run the Media-Dashboard.ps1 script to view the dashboard." -ForegroundColor Yellow
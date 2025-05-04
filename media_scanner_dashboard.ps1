# Media Scanner Dashboard
# This script generates an HTML dashboard for media files scanned by media_scanner_db.ps1

param (
    [string]$DatabasePath = "C:\MediaAnalyzer\media_scanner.db", # Match the path in media_scanner_db.ps1
    [string]$OutputPath = "C:\MediaAnalyzer\dashboard.html"
)

# Import required modules - make sure these are installed
# Install-Module -Name PSSQLite
Import-Module PSSQLite

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Error "Database file not found at: $DatabasePath"
    exit 1
}

# Now fetch data for the dashboard
try {
    # Get root folders - Adapted for media_info table structure
    $rootFolderQuery = @"
SELECT 
    DISTINCT substr(FilePath, 1, instr(FilePath, '\', 1, 3)) as folder_path
FROM 
    media_info
"@
    $rootFolders = Invoke-SqliteQuery -DataSource $DatabasePath -Query $rootFolderQuery
    
    # Get file statistics - Adapted for media_info table structure
    $statsQuery = @"
SELECT 
    COUNT(*) as total_files,
    SUM(FileSize) as total_size,
    COUNT(CASE WHEN FileExtension IN ('.mp4', '.mkv', '.avi', '.mov') THEN 1 END) as video_files,
    COUNT(CASE WHEN FileExtension IN ('.jpg', '.png', '.gif', '.bmp') THEN 1 END) as image_files,
    COUNT(CASE WHEN FileExtension IN ('.mp3', '.flac', '.wav', '.ogg') THEN 1 END) as audio_files,
    COUNT(CASE WHEN FileExtension NOT IN 
        ('.mp4', '.mkv', '.avi', '.mov', '.jpg', '.png', '.gif', '.bmp', '.mp3', '.flac', '.wav', '.ogg') 
        THEN 1 END) as other_files
FROM 
    media_info
"@
    $stats = Invoke-SqliteQuery -DataSource $DatabasePath -Query $statsQuery
    
    # If no stats were returned, initialize with zeros
    if (-not $stats) {
        $stats = [PSCustomObject]@{
            total_files = 0
            total_size = 0
            video_files = 0
            image_files = 0
            audio_files = 0
            other_files = 0
        }
    }
    
    # Format file size for display
    $formattedSize = if ($stats.total_size -ge 1GB) {
        "{0:N2} GB" -f ($stats.total_size / 1GB)
    } elseif ($stats.total_size -ge 1MB) {
        "{0:N2} MB" -f ($stats.total_size / 1MB)
    } else {
        "{0:N2} KB" -f ($stats.total_size / 1KB)
    }
    
} catch {
    Write-Error "Error querying database: $_"
    exit 1
}

# Generate HTML dashboard - Note we're using double quotes for PowerShell variables
$htmlHead = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Library Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .stats-card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .folder-card {
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .file-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .nav-tabs .nav-link {
            cursor: pointer;
        }
        .type-badge {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Media Library Dashboard</h1>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card stats-card">
                    <div class="card-body">
                        <h5 class="card-title">Total Files</h5>
                        <h2 class="card-text">$($stats.total_files)</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card">
                    <div class="card-body">
                        <h5 class="card-title">Total Size</h5>
                        <h2 class="card-text">$formattedSize</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card">
                    <div class="card-body">
                        <h5 class="card-title">File Types</h5>
                        <div class="d-flex justify-content-between">
                            <span class="badge bg-primary">Video: $($stats.video_files)</span>
                            <span class="badge bg-success">Audio: $($stats.audio_files)</span>
                            <span class="badge bg-info">Images: $($stats.image_files)</span>
                            <span class="badge bg-secondary">Other: $($stats.other_files)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <h2 class="mt-4 mb-3">Root Folders</h2>
"@

# Initialize HTML content with the header
$htmlContent = $htmlHead

# Add folder sections if any found
if ($rootFolders -and $rootFolders.Count -gt 0) {
    $folderId = 0
    foreach ($folder in $rootFolders) {
        $folderPath = $folder.folder_path
        $folderId++
        
        # Get files for this folder - Adapted for media_info table structure
        $folderFilesQuery = @"
SELECT 
    ID as id, 
    FileName as file_name, 
    FileSize as file_size, 
    FileExtension as file_type,
    CreatedDate as created_date,
    LastModifiedDate as modified_date,
    ScannedDate as scanned_date
FROM 
    media_info 
WHERE 
    FilePath LIKE '$folderPath%' 
ORDER BY 
    FileName
"@
        $folderFiles = Invoke-SqliteQuery -DataSource $DatabasePath -Query $folderFilesQuery
        
        # Count files by type for this folder
        $folderVideoFiles = ($folderFiles | Where-Object { $_.file_type -in ('.mp4', '.mkv', '.avi', '.mov') }).Count
        $folderAudioFiles = ($folderFiles | Where-Object { $_.file_type -in ('.mp3', '.flac', '.wav', '.ogg') }).Count
        $folderImageFiles = ($folderFiles | Where-Object { $_.file_type -in ('.jpg', '.png', '.gif', '.bmp') }).Count
        $folderOtherFiles = ($folderFiles | Where-Object { $_.file_type -notin ('.mp4', '.mkv', '.avi', '.mov', '.jpg', '.png', '.gif', '.bmp', '.mp3', '.flac', '.wav', '.ogg') }).Count
        $folderTotalFiles = $folderFiles.Count
        
        # Calculate folder size
        $folderSize = ($folderFiles | Measure-Object -Property file_size -Sum).Sum
        $formattedFolderSize = if ($folderSize -ge 1GB) {
            "{0:N2} GB" -f ($folderSize / 1GB)
        } elseif ($folderSize -ge 1MB) {
            "{0:N2} MB" -f ($folderSize / 1MB)
        } else {
            "{0:N2} KB" -f ($folderSize / 1KB)
        }
        
        $htmlContent += @"
        <div class="card folder-card" id="folder_$folderId">
            <div class="card-header">
                <h5 class="mb-0">$folderPath</h5>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-3">
                        <strong>Files:</strong> $folderTotalFiles
                    </div>
                    <div class="col-md-3">
                        <strong>Size:</strong> $formattedFolderSize
                    </div>
                    <div class="col-md-6">
                        <span class="badge bg-primary">Video: $folderVideoFiles</span>
                        <span class="badge bg-success">Audio: $folderAudioFiles</span>
                        <span class="badge bg-info">Images: $folderImageFiles</span>
                        <span class="badge bg-secondary">Other: $folderOtherFiles</span>
                    </div>
                </div>
                
                <ul class="nav nav-tabs" id="folderTabs_$folderId">
                    <li class="nav-item">
                        <a class="nav-link active" data-tab="all_$folderId">All Files</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="video_$folderId">Video</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="audio_$folderId">Audio</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="image_$folderId">Images</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="other_$folderId">Other</a>
                    </li>
                </ul>
                
                <div class="tab-content mt-3">
                    <div class="tab-pane active" id="all_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Created Date</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add files to the table
        foreach ($file in $folderFiles) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileCreatedDate = $file.created_date
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            # Set badge color based on file type
            $typeBadgeClass = switch -Wildcard ($fileType) {
                {$_ -in '.mp4', '.mkv', '.avi', '.mov'} { 'bg-primary' }
                {$_ -in '.mp3', '.flac', '.wav', '.ogg'} { 'bg-success' }
                {$_ -in '.jpg', '.png', '.gif', '.bmp'} { 'bg-info' }
                default { 'bg-secondary' }
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td><span class="badge $typeBadgeClass">$fileType</span></td>
                                        <td>$formattedFileSize</td>
                                        <td>$fileCreatedDate</td>
                                    </tr>
"@
        }
        
        # Add tabs for filtered views
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="video_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Created Date</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add video files
        foreach ($file in ($folderFiles | Where-Object { $_.file_type -in ('.mp4', '.mkv', '.avi', '.mov') })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileCreatedDate = $file.created_date
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td><span class="badge bg-primary">$fileType</span></td>
                                        <td>$formattedFileSize</td>
                                        <td>$fileCreatedDate</td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="audio_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Created Date</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add audio files
        foreach ($file in ($folderFiles | Where-Object { $_.file_type -in ('.mp3', '.flac', '.wav', '.ogg') })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileCreatedDate = $file.created_date
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td><span class="badge bg-success">$fileType</span></td>
                                        <td>$formattedFileSize</td>
                                        <td>$fileCreatedDate</td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="image_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Created Date</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add image files
        foreach ($file in ($folderFiles | Where-Object { $_.file_type -in ('.jpg', '.png', '.gif', '.bmp') })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileCreatedDate = $file.created_date
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td><span class="badge bg-info">$fileType</span></td>
                                        <td>$formattedFileSize</td>
                                        <td>$fileCreatedDate</td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="other_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Created Date</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add other files
        foreach ($file in ($folderFiles | Where-Object { $_.file_type -notin ('.mp4', '.mkv', '.avi', '.mov', '.jpg', '.png', '.gif', '.bmp', '.mp3', '.flac', '.wav', '.ogg') })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileCreatedDate = $file.created_date
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td><span class="badge bg-secondary">$fileType</span></td>
                                        <td>$formattedFileSize</td>
                                        <td>$fileCreatedDate</td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"@
    }
} else {
    $htmlContent += @"
        <div class="alert alert-info">
            No folders found in the database. Please run the media scanner first.
        </div>
"@
}

# Add JavaScript section using SINGLE quotes to prevent PowerShell parsing
$jsScript = @'
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        $(document).ready(function() {
            // Tab switching functionality
            $('.nav-link').on('click', function() {
                const tabId = $(this).data('tab');
                const parentTabs = $(this).parent().parent();
                const folderId = parentTabs.attr('id').split('_')[1];
                
                // Remove active class from all tabs and content
                parentTabs.find('.nav-link').removeClass('active');
                $('#folder_' + folderId + ' .tab-content').children().removeClass('active');
                
                // Add active class to clicked tab and corresponding content
                $(this).addClass('active');
                $('#' + tabId).addClass('active');
            });
        });
    </script>
</body>
</html>
'@

# Combine the HTML and JavaScript
$htmlContent += $jsScript

# Write the HTML to file
$htmlContent | Out-File -FilePath $OutputPath -Encoding utf8

Write-Host "Dashboard generated at: $OutputPath"
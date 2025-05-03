# Media Scanner Dashboard
# This script generates an HTML dashboard for media files

param (
    [string]$DatabasePath = "C:\MediaAnalyzer\media_scanner.db",
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
    # Get root folders
    $rootFolderQuery = "SELECT DISTINCT folder_path FROM media_files;"
    $rootFolders = Invoke-SqliteQuery -DataSource $DatabasePath -Query $rootFolderQuery
    
    # Get file statistics
    $statsQuery = @"
SELECT 
    COUNT(*) as total_files,
    SUM(file_size) as total_size,
    COUNT(CASE WHEN status = 'new' THEN 1 END) as new_files,
    COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_files,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_files
FROM media_files;
"@
    $stats = Invoke-SqliteQuery -DataSource $DatabasePath -Query $statsQuery
    
    # If no stats were returned, initialize with zeros
    if (-not $stats) {
        $stats = [PSCustomObject]@{
            total_files = 0
            total_size = 0
            new_files = 0
            processed_files = 0
            error_files = 0
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
    <title>Media Scanner Dashboard</title>
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
        .status-badge {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Media Scanner Dashboard</h1>
        
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
                        <h5 class="card-title">Status</h5>
                        <div class="d-flex justify-content-between">
                            <span class="badge bg-primary">New: $($stats.new_files)</span>
                            <span class="badge bg-success">Processed: $($stats.processed_files)</span>
                            <span class="badge bg-danger">Error: $($stats.error_files)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <h2 class="mt-4 mb-3">Folders</h2>
"@

# Initialize HTML content with the header
$htmlContent = $htmlHead

# Add folder sections if any found
if ($rootFolders -and $rootFolders.Count -gt 0) {
    $folderId = 0
    foreach ($folder in $rootFolders) {
        $folderPath = $folder.folder_path
        $folderId++
        
        # Get files for this folder
        $folderFilesQuery = "SELECT id, file_name, file_size, file_type, status FROM media_files WHERE folder_path = '$folderPath' ORDER BY file_name;"
        $folderFiles = Invoke-SqliteQuery -DataSource $DatabasePath -Query $folderFilesQuery
        
        # Count files by status for this folder
        $folderNewFiles = ($folderFiles | Where-Object { $_.status -eq 'new' }).Count
        $folderProcessedFiles = ($folderFiles | Where-Object { $_.status -eq 'processed' }).Count
        $folderErrorFiles = ($folderFiles | Where-Object { $_.status -eq 'error' }).Count
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
                        <span class="badge bg-primary">New: $folderNewFiles</span>
                        <span class="badge bg-success">Processed: $folderProcessedFiles</span>
                        <span class="badge bg-danger">Error: $folderErrorFiles</span>
                    </div>
                </div>
                
                <ul class="nav nav-tabs" id="folderTabs_$folderId">
                    <li class="nav-item">
                        <a class="nav-link active" data-tab="all_$folderId">All Files</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="new_$folderId">New</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="processed_$folderId">Processed</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="error_$folderId">Error</a>
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
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add files to the table
        foreach ($file in $folderFiles) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            $fileStatus = $file.status
            
            # Format file size
            $fileSize = $file.file_size
            $formattedFileSize = if ($fileSize -ge 1GB) {
                "{0:N2} GB" -f ($fileSize / 1GB)
            } elseif ($fileSize -ge 1MB) {
                "{0:N2} MB" -f ($fileSize / 1MB)
            } else {
                "{0:N2} KB" -f ($fileSize / 1KB)
            }
            
            # Set badge color based on status
            $statusBadgeClass = switch ($fileStatus) {
                'new' { 'bg-primary' }
                'processed' { 'bg-success' }
                'error' { 'bg-danger' }
                default { 'bg-secondary' }
            }
            
            $htmlContent += @"
                                    <tr>
                                        <td>$fileName</td>
                                        <td>$fileType</td>
                                        <td>$formattedFileSize</td>
                                        <td><span class="badge $statusBadgeClass status-badge" data-id="$fileId" data-current="$fileStatus">$fileStatus</span></td>
                                    </tr>
"@
        }
        
        # Add tabs for filtered views
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="new_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add new files
        foreach ($file in ($folderFiles | Where-Object { $_.status -eq 'new' })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            
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
                                        <td>$fileType</td>
                                        <td>$formattedFileSize</td>
                                        <td><span class="badge bg-primary status-badge" data-id="$fileId" data-current="new">new</span></td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="processed_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add processed files
        foreach ($file in ($folderFiles | Where-Object { $_.status -eq 'processed' })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            
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
                                        <td>$fileType</td>
                                        <td>$formattedFileSize</td>
                                        <td><span class="badge bg-success status-badge" data-id="$fileId" data-current="processed">processed</span></td>
                                    </tr>
"@
        }
        
        $htmlContent += @"
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane" id="error_$folderId">
                        <div class="file-list">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>File Name</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
"@

        # Add error files
        foreach ($file in ($folderFiles | Where-Object { $_.status -eq 'error' })) {
            $fileId = $file.id
            $fileName = $file.file_name
            $fileType = $file.file_type
            
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
                                        <td>$fileType</td>
                                        <td>$formattedFileSize</td>
                                        <td><span class="badge bg-danger status-badge" data-id="$fileId" data-current="error">error</span></td>
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
            
            // Status badge click functionality
            $('.status-badge').on('click', function() {
                const fileId = $(this).data('id');
                const currentStatus = $(this).data('current');
                
                // Here you could implement AJAX to update status in the database
                // For now, just cycle through statuses
                const newStatus = currentStatus === 'new' ? 'processed' :
                                  currentStatus === 'processed' ? 'error' : 'new';
                
                // Update badge appearance and data
                $(this).parent().html('<span class="badge status-badge ' + 
                    (newStatus === 'new' ? 'bg-primary' : 
                     newStatus === 'processed' ? 'bg-success' : 'bg-danger') + 
                    '" data-id="' + fileId + '" data-current="' + newStatus + '">' + newStatus + '</span>');
                
                // Reattach click handler
                $('.status-badge').off('click').on('click', function() {
                    const fileId = $(this).data('id');
                    const currentStatus = $(this).data('current');
                    
                    const newStatus = currentStatus === 'new' ? 'processed' :
                                     currentStatus === 'processed' ? 'error' : 'new';
                    
                    $(this).parent().html('<span class="badge status-badge ' + 
                        (newStatus === 'new' ? 'bg-primary' : 
                         newStatus === 'processed' ? 'bg-success' : 'bg-danger') + 
                        '" data-id="' + fileId + '" data-current="' + newStatus + '">' + newStatus + '</span>');
                });
                
                // In a real implementation, you would also update the database
                // For example:
                /*
                $.ajax({
                    url: 'update_status.php',
                    method: 'POST',
                    data: {
                        fileId: fileId,
                        newStatus: newStatus
                    },
                    success: function(response) {
                        console.log('Status updated');
                    }
                });
                */
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

# Also create a PowerShell function to update file status
$updateScriptPath = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($OutputPath), "update_status.ps1")

$updateScriptContent = @"
# Update Media File Status
# This script updates the status of a media file in the database

param (
    [Parameter(Mandatory=`$true)]
    [int]`$FileId,
    
    [Parameter(Mandatory=`$true)]
    [ValidateSet('new', 'processed', 'error')]
    [string]`$NewStatus,
    
    [string]`$DatabasePath = "C:\MediaAnalyzer\media_scanner.db"
)

# Import required modules
Import-Module PSSQLite

# Check if database exists
if (-not (Test-Path `$DatabasePath)) {
    Write-Error "Database file not found at: `$DatabasePath"
    exit 1
}

# Update the file status
try {
    `$updateQuery = "UPDATE media_files SET status = '`$NewStatus' WHERE id = `$FileId;"
    Invoke-SqliteQuery -DataSource `$DatabasePath -Query `$updateQuery
    Write-Host "File status updated successfully."
} catch {
    Write-Error "Error updating file status: `$_"
    exit 1
}
"@

$updateScriptContent | Out-File -FilePath $updateScriptPath -Encoding utf8

Write-Host "Status update script generated at: $updateScriptPath"
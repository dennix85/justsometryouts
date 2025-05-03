# Media Scanner Dashboard
# This script creates an interactive HTML dashboard for media files scanned by media_scanner_db.ps1
# Dependencies: Install-Module -Name PSSQLite

param (
    [Parameter(Mandatory=$true)]
    [string]$DatabasePath,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "MediaDashboard.html"
)

# Ensure SQLite module is available
if (-not (Get-Module -ListAvailable -Name PSSQLite)) {
    Write-Error "PSSQLite module is required. Please install it using: Install-Module -Name PSSQLite"
    exit 1
}

Import-Module PSSQLite

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Error "Database file not found at: $DatabasePath"
    exit 1
}

# Query to get all root folders
$rootFoldersQuery = "SELECT DISTINCT root_folder FROM media_files ORDER BY root_folder"
$rootFolders = Invoke-SqliteQuery -DataSource $DatabasePath -Query $rootFoldersQuery

# Prepare data for each root folder
$folderData = @{}

foreach ($folder in $rootFolders) {
    $rootFolder = $folder.root_folder
    
    # Get successful files (status = 'ok')
    $okFilesQuery = "SELECT * FROM media_files WHERE root_folder = '$rootFolder' AND status = 'ok'"
    $okFiles = Invoke-SqliteQuery -DataSource $DatabasePath -Query $okFilesQuery
    
    # Get suspicious files (status = 'suspicious')
    $suspiciousFilesQuery = "SELECT * FROM media_files WHERE root_folder = '$rootFolder' AND status = 'suspicious'"
    $suspiciousFiles = Invoke-SqliteQuery -DataSource $DatabasePath -Query $suspiciousFilesQuery
    
    # Get manually added files (source = 'manual')
    $manualFilesQuery = "SELECT * FROM media_files WHERE root_folder = '$rootFolder' AND source = 'manual'"
    $manualFiles = Invoke-SqliteQuery -DataSource $DatabasePath -Query $manualFilesQuery
    
    # Store data for this folder
    $folderData[$rootFolder] = @{
        OkFiles = $okFiles
        SuspiciousFiles = $suspiciousFiles
        ManualFiles = $manualFiles
        TotalFiles = $okFiles.Count + $suspiciousFiles.Count + $manualFiles.Count
        Stats = @{
            TotalOk = $okFiles.Count
            TotalSuspicious = $suspiciousFiles.Count
            TotalManual = $manualFiles.Count
            FileTypes = @{}
            MediaDurations = @{}
        }
    }
    
    # Gather statistics for charts
    $allFiles = $okFiles + $suspiciousFiles + $manualFiles
    foreach ($file in $allFiles) {
        $extension = [System.IO.Path]::GetExtension($file.filename).ToLower()
        
        if (-not $folderData[$rootFolder].Stats.FileTypes.ContainsKey($extension)) {
            $folderData[$rootFolder].Stats.FileTypes[$extension] = 0
        }
        $folderData[$rootFolder].Stats.FileTypes[$extension]++
        
        # Group durations for histogram
        if ($file.duration) {
            $durationMinutes = [math]::Floor($file.duration / 60)
            $durationBucket = switch ($durationMinutes) {
                {$_ -lt 5} { "0-5 min" }
                {$_ -lt 10} { "5-10 min" }
                {$_ -lt 30} { "10-30 min" }
                {$_ -lt 60} { "30-60 min" }
                {$_ -lt 120} { "1-2 hours" }
                default { "2+ hours" }
            }
            
            if (-not $folderData[$rootFolder].Stats.MediaDurations.ContainsKey($durationBucket)) {
                $folderData[$rootFolder].Stats.MediaDurations[$durationBucket] = 0
            }
            $folderData[$rootFolder].Stats.MediaDurations[$durationBucket]++
        }
    }
}

# Function to convert file data to HTML table
function ConvertTo-HtmlTable {
    param (
        [Parameter(Mandatory=$true)]
        [Array]$Files,
        
        [Parameter(Mandatory=$true)]
        [string]$TableId,
        
        [Parameter(Mandatory=$false)]
        [switch]$AddStatusChange
    )
    
    $htmlRows = $Files | ForEach-Object {
        $id = $_.id
        $file = $_.filename
        $duration = if ($_.duration) { [TimeSpan]::FromSeconds($_.duration).ToString("hh\:mm\:ss") } else { "N/A" }
        $creationDate = if ($_.creation_date) { $_.creation_date } else { "N/A" }
        $size = if ($_.filesize) { "$([math]::Round($_.filesize / 1MB, 2)) MB" } else { "N/A" }
        $status = $_.status
        
        $statusCell = if ($AddStatusChange) {
            "<td>$status <button class='status-btn' data-id='$id' data-current='$status'>Mark as OK</button></td>"
        } else {
            "<td>$status</td>"
        }
        
        "<tr>
            <td>$id</td>
            <td>$file</td>
            <td>$duration</td>
            <td>$creationDate</td>
            <td>$size</td>
            $statusCell
        </tr>"
    }
    
    $headers = "<tr>
        <th>ID</th>
        <th>Filename</th>
        <th>Duration</th>
        <th>Creation Date</th>
        <th>Size</th>
        <th>Status</th>
    </tr>"
    
    return "<table id='$TableId' class='display'>
        <thead>$headers</thead>
        <tbody>$($htmlRows -join '')</tbody>
    </table>"
}

# Generate HTML file with dashboard
$html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Scanner Dashboard</title>
    
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/css/jquery.dataTables.min.css">
    
    <!-- jQuery and DataTables JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/datatables/1.10.21/js/jquery.dataTables.min.js"></script>
    
    <!-- Chart.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.1/chart.min.js"></script>
    
    <!-- Custom CSS -->
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .folder-section {
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }
        
        .folder-header {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .folder-stats {
            display: flex;
            gap: 20px;
        }
        
        .stat-box {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        .stat-box span {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 15px;
            border-bottom: 1px solid #ddd;
        }
        
        .tab {
            padding: 10px 15px;
            cursor: pointer;
            border: 1px solid transparent;
            border-bottom: none;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
        }
        
        .tab.active {
            background-color: #fff;
            border-color: #ddd;
            border-bottom-color: transparent;
        }
        
        .tab-content {
            display: none;
            padding: 15px;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .charts-container {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }
        
        .chart-box {
            width: 48%;
            padding: 15px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
        }

        table.display {
            width: 100% !important;
        }
        
        .status-btn {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 8px;
            cursor: pointer;
            margin-left: 10px;
        }
        
        .status-btn:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>Media Scanner Dashboard</h1>
        
        <div class="database-info">
            <p><strong>Database Path:</strong> $DatabasePath</p>
            <p><strong>Dashboard Generated:</strong> $(Get-Date)</p>
        </div>
        
"@

# Generate HTML for each root folder
foreach ($folderKey in $folderData.Keys) {
    $folder = $folderData[$folderKey]
    $safeFolderId = $folderKey -replace '[^a-zA-Z0-9]', '_'
    
    $html += @"
        <div class="folder-section" id="folder_$safeFolderId">
            <div class="folder-header">
                <h2>$folderKey</h2>
                <div class="folder-stats">
                    <div class="stat-box">OK Files: <span>$($folder.Stats.TotalOk)</span></div>
                    <div class="stat-box">Suspicious Files: <span>$($folder.Stats.TotalSuspicious)</span></div>
                    <div class="stat-box">Manual Files: <span>$($folder.Stats.TotalManual)</span></div>
                    <div class="stat-box">Total Files: <span>$($folder.TotalFiles)</span></div>
                </div>
            </div>
            
            <div class="tabs" id="tabs_$safeFolderId">
                <div class="tab active" data-tab="ok_$safeFolderId">OK Files</div>
                <div class="tab" data-tab="suspicious_$safeFolderId">Suspicious Files</div>
                <div class="tab" data-tab="manual_$safeFolderId">Manually Added Files</div>
                <div class="tab" data-tab="charts_$safeFolderId">Charts</div>
            </div>
            
            <div class="tab-content active" id="ok_$safeFolderId">
                $(ConvertTo-HtmlTable -Files $folder.OkFiles -TableId "table_ok_$safeFolderId")
            </div>
            
            <div class="tab-content" id="suspicious_$safeFolderId">
                $(ConvertTo-HtmlTable -Files $folder.SuspiciousFiles -TableId "table_suspicious_$safeFolderId" -AddStatusChange)
            </div>
            
            <div class="tab-content" id="manual_$safeFolderId">
                $(ConvertTo-HtmlTable -Files $folder.ManualFiles -TableId "table_manual_$safeFolderId")
            </div>
            
            <div class="tab-content" id="charts_$safeFolderId">
                <div class="charts-container">
                    <div class="chart-box">
                        <h3>File Types Distribution</h3>
                        <canvas id="fileTypesChart_$safeFolderId"></canvas>
                    </div>
                    <div class="chart-box">
                        <h3>Media Duration Distribution</h3>
                        <canvas id="durationChart_$safeFolderId"></canvas>
                    </div>
                </div>
                <div class="charts-container" style="margin-top: 20px;">
                    <div class="chart-box">
                        <h3>Files Status Distribution</h3>
                        <canvas id="statusChart_$safeFolderId"></canvas>
                    </div>
                </div>
            </div>
        </div>
"@
}

# Complete the HTML with JavaScript for interactivity
$html += @"
    </div>
    
    <script>
        // Initialize DataTables and other JS functionality after document is loaded
        $(document).ready(function() {
            // Initialize all DataTables
            $('table.display').DataTable({
                responsive: true,
                order: [[0, 'asc']],
                pageLength: 10,
                lengthMenu: [10, 25, 50, 100]
            });
            
            // Tab switching functionality
            $('.tab').click(function() {
                const tabId = $(this).data('tab');
                const parentTabs = $(this).parent();
                const folderId = parentTabs.attr('id').replace('tabs_', '');
                
                // Remove active class from current tabs and content
                parentTabs.find('.tab').removeClass('active');
                $(`#folder_\${folderId} .tab-content`).removeClass('active');
                
                // Add active class to clicked tab and its content
                $(this).addClass('active');
                $(`#\${tabId}`).addClass('active');
            });
            
            // Handle status change buttons
            $('.status-btn').click(function() {
                const fileId = $(this).data('id');
                const currentStatus = $(this).data('current');
                
                // In a real implementation, this would update the database
                alert(`Status would be updated in database: File ID \${fileId} from "\${currentStatus}" to "ok"`);
                
                // Update the display (in real implementation, you might refresh data from DB)
                $(this).parent().text('ok');
            });
            
            // Initialize charts for each folder
"@

# Generate JavaScript for charts in each folder
foreach ($folderKey in $folderData.Keys) {
    $folder = $folderData[$folderKey]
    $safeFolderId = $folderKey -replace '[^a-zA-Z0-9]', '_'
    
    # File types chart
    $fileTypeLabels = $folder.Stats.FileTypes.Keys | ForEach-Object { "`"$_`"" }
    $fileTypeValues = $folder.Stats.FileTypes.Values
    
    # Duration chart
    $durationLabels = $folder.Stats.MediaDurations.Keys | ForEach-Object { "`"$_`"" }
    $durationValues = $folder.Stats.MediaDurations.Values
    
    # Status chart
    $statusLabels = @('"OK"', '"Suspicious"', '"Manual"')
    $statusValues = @($folder.Stats.TotalOk, $folder.Stats.TotalSuspicious, $folder.Stats.TotalManual)
    
    $html += @"
            // Charts for folder $folderKey
            new Chart(document.getElementById('fileTypesChart_$safeFolderId'), {
                type: 'pie',
                data: {
                    labels: [$($fileTypeLabels -join ',')],
                    datasets: [{
                        data: [$($fileTypeValues -join ',')],
                        backgroundColor: [
                            '#4CAF50', '#2196F3', '#FFC107', '#F44336', '#9C27B0', 
                            '#3F51B5', '#00BCD4', '#009688', '#FF9800', '#795548'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
            
            new Chart(document.getElementById('durationChart_$safeFolderId'), {
                type: 'bar',
                data: {
                    labels: [$($durationLabels -join ',')],
                    datasets: [{
                        label: 'Number of Files',
                        data: [$($durationValues -join ',')],
                        backgroundColor: '#2196F3'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            new Chart(document.getElementById('statusChart_$safeFolderId'), {
                type: 'doughnut',
                data: {
                    labels: [$($statusLabels -join ',')],
                    datasets: [{
                        data: [$($statusValues -join ',')],
                        backgroundColor: ['#4CAF50', '#FF9800', '#2196F3']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
"@
}

# Complete the JavaScript and HTML
$html += @"
        });
    </script>
</body>
</html>
"@

# Write HTML to file
$html | Out-File -FilePath $OutputPath -Encoding UTF8

Write-Host "Dashboard generated successfully at: $OutputPath"
Write-Host "Open this HTML file in your browser to view the dashboard."

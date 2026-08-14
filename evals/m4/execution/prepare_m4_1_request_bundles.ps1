[CmdletBinding()]
param(
    [switch]$SelfTest,
    [switch]$CheckAll,
    [string]$TaskId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-BytesSha256([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString(
            $sha.ComputeHash($Bytes)
        )).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-TextSha256([string]$Text) {
    return Get-BytesSha256 ([System.Text.Encoding]::UTF8.GetBytes($Text))
}

function Get-FileSha256([string]$Path) {
    return Get-BytesSha256 ([System.IO.File]::ReadAllBytes($Path))
}

function Resolve-RepoFile([string]$RepoRoot, [string]$RelativePath) {
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    $rootPrefix = $root + [System.IO.Path]::DirectorySeparatorChar
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $root $RelativePath))
    if (-not $candidate.StartsWith(
        $rootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'repository_path_escape'
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw 'repository_file_missing'
    }
    return $candidate
}

function Read-Json([string]$Path) {
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Write-Result(
    [string]$Status,
    [int]$CheckedTaskCount,
    [object[]]$Mismatches
) {
    $result = [ordered]@{
        status = $Status
        checked_task_count = $CheckedTaskCount
        mismatches = [object[]]$Mismatches
        side_effects = [object[]]@()
        powershell_version = $PSVersionTable.PSVersion.ToString()
        clr_version = [System.Environment]::Version.ToString()
    }
    Write-Output ($result | ConvertTo-Json -Depth 5 -Compress)
}

function Test-KnownVectors {
    $emptyExpected = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    $abcExpected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    if ((Get-BytesSha256 ([byte[]]@())) -ne $emptyExpected) {
        throw 'empty_sha256_mismatch'
    }
    if ((Get-BytesSha256 ([System.Text.Encoding]::UTF8.GetBytes('abc'))) -ne $abcExpected) {
        throw 'abc_sha256_mismatch'
    }
}

function Test-PreparedTask(
    [object]$Task,
    [object]$SourceTask,
    [string]$RepoRoot
) {
    $mismatches = @()
    $sourceTaskId = [string]$Task.source_task_id
    $expectedTaskId = 'M4.1-' + $sourceTaskId.Substring(3)
    if ([string]$Task.task_id -ne $expectedTaskId) {
        $mismatches += ([string]$Task.task_id + ':task_id_mismatch')
    }
    $sourceBatchId = [string]$Task.source_batch_id
    $expectedBatchId = 'M4.1-BATCH-' + $sourceBatchId.Substring(9)
    if ([string]$Task.batch_id -ne $expectedBatchId) {
        $mismatches += ([string]$Task.task_id + ':batch_id_mismatch')
    }

    $inheritedFields = @(
        'case_id',
        'domain',
        'case_type',
        'arm_id',
        'case_path',
        'case_sha256',
        'user_input_sha256',
        'task_protocol_sha256',
        'variant_instruction_path',
        'variant_instruction_sha256',
        'rubric_sha256',
        'execution_constraints_sha256'
    )
    foreach ($field in $inheritedFields) {
        if ([string]$Task.$field -ne [string]$SourceTask.$field) {
            $mismatches += ([string]$Task.task_id + ':' + $field + '_source_mismatch')
        }
    }

    $casePath = Resolve-RepoFile $RepoRoot ([string]$Task.case_path)
    if ((Get-FileSha256 $casePath) -ne [string]$Task.case_sha256) {
        $mismatches += ([string]$Task.task_id + ':case_sha256_mismatch')
    }
    $case = Read-Json $casePath
    if ((Get-TextSha256 ([string]$case.user_input)) -ne [string]$Task.user_input_sha256) {
        $mismatches += ([string]$Task.task_id + ':user_input_sha256_mismatch')
    }

    $protocolPath = Resolve-RepoFile $RepoRoot 'evals/m4/task-protocol.md'
    if ((Get-FileSha256 $protocolPath) -ne [string]$Task.task_protocol_sha256) {
        $mismatches += ([string]$Task.task_id + ':task_protocol_sha256_mismatch')
    }
    if ($null -ne $Task.variant_instruction_path) {
        $variantPath = Resolve-RepoFile $RepoRoot ([string]$Task.variant_instruction_path)
        if ((Get-FileSha256 $variantPath) -ne [string]$Task.variant_instruction_sha256) {
            $mismatches += ([string]$Task.task_id + ':variant_instruction_sha256_mismatch')
        }
    }
    $rubricPath = Resolve-RepoFile $RepoRoot 'evals/m4/judge-rubric.json'
    if ((Get-FileSha256 $rubricPath) -ne [string]$Task.rubric_sha256) {
        $mismatches += ([string]$Task.task_id + ':rubric_sha256_mismatch')
    }

    $variantHash = [string]$Task.variant_instruction_sha256
    if ([string]::IsNullOrEmpty($variantHash)) {
        $variantHash = 'NONE'
    }
    $fields = @(
        'm4.1-request-binding-v1',
        [string]$Task.task_id,
        [string]$Task.source_task_id,
        [string]$Task.blind_id,
        [string]$Task.case_sha256,
        [string]$Task.user_input_sha256,
        [string]$Task.task_protocol_sha256,
        $variantHash,
        [string]$Task.rubric_sha256,
        [string]$Task.execution_constraints_sha256
    )
    $framed = ($fields -join "`n") + "`n"
    if ((Get-TextSha256 $framed) -ne [string]$Task.request_binding_sha256) {
        $mismatches += ([string]$Task.task_id + ':request_binding_sha256_mismatch')
    }
    return [object[]]$mismatches
}

$modeCount = 0
if ($SelfTest.IsPresent) { $modeCount += 1 }
if ($CheckAll.IsPresent) { $modeCount += 1 }
if (-not [string]::IsNullOrEmpty($TaskId)) { $modeCount += 1 }
if ($modeCount -ne 1) {
    throw 'exactly_one_mode_required'
}

Test-KnownVectors
if ($SelfTest.IsPresent) {
    Write-Result 'SELF_TEST_PASSED' 0 @()
    exit 0
}

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$manifestPath = Resolve-RepoFile $repoRoot 'evals/m4/revisions/m4.1/preparation-manifest.json'
$baseManifestPath = Resolve-RepoFile $repoRoot 'evals/m4/preparation-manifest.json'
$manifest = Read-Json $manifestPath
$baseManifest = Read-Json $baseManifestPath
$mismatches = @()

$helperPath = Resolve-RepoFile $repoRoot ([string]$manifest.execution_helper.path)
if ((Get-FileSha256 $helperPath) -ne [string]$manifest.execution_helper.raw_sha256) {
    $mismatches += 'execution_helper_sha256_mismatch'
}

$sourceTasks = @{}
foreach ($sourceTask in $baseManifest.tasks) {
    $sourceTasks[[string]$sourceTask.task_id] = $sourceTask
}

if ($CheckAll.IsPresent) {
    $selectedTasks = @($manifest.tasks)
}
else {
    $selectedTasks = @($manifest.tasks | Where-Object { [string]$_.task_id -eq $TaskId })
    if ($selectedTasks.Count -ne 1) {
        $mismatches += 'task_id_not_found'
    }
}

$checkedTaskCount = 0
foreach ($task in $selectedTasks) {
    $sourceTaskId = [string]$task.source_task_id
    if (-not $sourceTasks.ContainsKey($sourceTaskId)) {
        $mismatches += ([string]$task.task_id + ':source_task_missing')
        continue
    }
    $mismatches += @(Test-PreparedTask $task $sourceTasks[$sourceTaskId] $repoRoot)
    $checkedTaskCount += 1
}

if ($mismatches.Count -eq 0) {
    Write-Result 'VERIFIED' $checkedTaskCount @()
    exit 0
}
Write-Result 'INVALID' $checkedTaskCount ([object[]]$mismatches)
exit 1

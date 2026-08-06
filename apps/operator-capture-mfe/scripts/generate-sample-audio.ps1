<#
.SYNOPSIS
    Regenerates the sample operator interview audio shipped with the capture PWA.

.DESCRIPTION
    Narrates services/knowledge-orchestrator/fixtures/interview_transcript.json using
    the Windows speech synthesiser, so the sample audio and the transcript the backend
    returns for it stay in lock-step. Anyone importing the sample hears exactly the
    interview they then see transcribed.

    Output is 16 kHz mono 16-bit PCM, the format Azure AI Speech expects, which also
    keeps the committed asset small.

    The interview is synthetic (fictional persona OP-DEMO-014) and contains no real
    personal data, so it is safe to commit and to replay in demos.

.EXAMPLE
    pwsh -File apps/operator-capture-mfe/scripts/generate-sample-audio.ps1
#>
[CmdletBinding()]
param(
    [string] $TranscriptPath,
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
if (-not $TranscriptPath) {
    $TranscriptPath = Join-Path $repoRoot 'services\knowledge-orchestrator\fixtures\interview_transcript.json'
}
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot 'apps\operator-capture-mfe\public\samples\blast-furnace-hearth-cooling-en.wav'
}

if (-not (Test-Path $TranscriptPath)) {
    throw "Transcript fixture not found: $TranscriptPath"
}

Add-Type -AssemblyName System.Speech

$fixture = Get-Content -Raw -LiteralPath $TranscriptPath | ConvertFrom-Json
$segments = @($fixture.segments)
if ($segments.Count -eq 0) {
    throw "Fixture $TranscriptPath contains no segments."
}

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $installed = @($synth.GetInstalledVoices() |
        Where-Object { $_.Enabled } |
        ForEach-Object { $_.VoiceInfo })
    if ($installed.Count -eq 0) {
        throw 'No enabled speech voices are installed on this machine.'
    }

    # Two distinct voices make the interviewer and the operator easy to tell apart.
    $female = $installed | Where-Object { $_.Gender -eq 'Female' } | Select-Object -First 1
    $male = $installed | Where-Object { $_.Gender -eq 'Male' } | Select-Object -First 1
    $interviewerVoice = if ($female) { $female.Name } else { $installed[0].Name }
    $operatorVoice = if ($male) { $male.Name } elseif ($installed.Count -gt 1) { $installed[1].Name } else { $installed[0].Name }

    Write-Host "Interviewer voice: $interviewerVoice"
    Write-Host "Operator voice:    $operatorVoice"

    $prompt = New-Object System.Speech.Synthesis.PromptBuilder
    foreach ($segment in $segments) {
        $voice = if ($segment.speaker -eq 'interviewer') { $interviewerVoice } else { $operatorVoice }
        $prompt.StartVoice($voice)
        $prompt.AppendText([string]$segment.text)
        $prompt.EndVoice()
        $prompt.AppendBreak([System.Speech.Synthesis.PromptBreak]::Medium)
    }

    $outDir = Split-Path -Parent $OutputPath
    if (-not (Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }

    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
        16000,
        [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono)

    # Slightly slower than default: plant procedures are dictated deliberately.
    $synth.Rate = -1
    $synth.SetOutputToWaveFile($OutputPath, $format)
    $synth.Speak($prompt)
    $synth.SetOutputToNull()
}
finally {
    $synth.Dispose()
}

$file = Get-Item -LiteralPath $OutputPath
$seconds = [math]::Round(($file.Length - 44) / (16000 * 2), 1)
Write-Host "Wrote $($file.FullName)"
Write-Host "Size: $([math]::Round($file.Length / 1MB, 2)) MB, duration: $seconds s, segments: $($segments.Count)"

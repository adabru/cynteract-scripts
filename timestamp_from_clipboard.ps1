# Get clipboard content
$clip = Get-Clipboard

# Extract timestamp, author, and message using regex
if ($clip -match '^\[(.*?)\]\s+([^:]+):\s*(.*)') {
    $timestamp = $matches[1]
    $author = $matches[2].Trim()
    $message = $matches[3] + "`n" + ($clip -split "`n", 2)[1]
    $message = $message.Trim()

    # Replace newlines in the message with non-breaking newlines (U+2028)
    $message = $message -replace "`r?`n", [char]0x2028

    # Compose output: time \t message \t\t author
    $output = "$timestamp`t$message`t`t$author"

    # Copy result to clipboard
    Set-Clipboard -Value $output

    # Output result
    Write-Host "Extracted and copied: $output"
}
else {
    Write-Host "No valid message format found in clipboard content."
}

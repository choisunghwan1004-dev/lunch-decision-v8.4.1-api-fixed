param([string]$Branch='feature/v8.5.1-ai-local-news')
$ErrorActionPreference='Stop'
$root=git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { throw 'Git clone folder required' }
Set-Location $root
if ((git branch --show-current).Trim() -ne $Branch) { throw 'Switch to the feature branch before uploading' }
$files=@('v84_integrated/public/admin.html','v84_integrated/news-service')
git add -- $files
$names=@(git diff --cached --name-only)
if ($names | Where-Object {$_ -match '(^|/)\.env($|\.)|\.pem$|secret'}) {
 git reset -- $files
 throw 'Sensitive file detected; push cancelled'
}
if ($names.Count -eq 0) { Write-Host 'No modified files'; exit 0 }
git diff --cached --stat
git commit -m ('update(news): changed files ' + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
if ($LASTEXITCODE -ne 0) {throw 'git commit failed'}
git push -u origin $Branch
if ($LASTEXITCODE -ne 0) {throw 'git push failed'}
Write-Host 'Changed files uploaded successfully'

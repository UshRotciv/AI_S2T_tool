Param(
  [string]$BaseUrl = 'http://localhost:8001'
)

function Invoke-DebugSample {
  param([string]$q, [int]$k = 5)
  $enc = [System.Uri]::EscapeDataString($q)
  $url = "$BaseUrl/api/debug/sample?q=$enc&k=$k"
  try {
    return Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 60
  } catch {
    return @{ error = $_.Exception.Message; url = $url }
  }
}

function Invoke-Ask {
  param([string]$q)
  $body = @{ question = $q } | ConvertTo-Json -Depth 5
  try {
    return Invoke-RestMethod -Uri "$BaseUrl/api/ask" -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 120
  } catch {
    return @{ error = $_.Exception.Message }
  }
}

$tests = @(
  @{ name = '標題測試'; q = '印表機發現無人拿走的機密文件' },
  @{ name = 'questionLabel測試'; q = '你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？' },
  @{ name = '資安範疇自然語言'; q = '在辦公室如果看到別人的機密文件遺留在印表機該怎麼處理才最合規？' },
  @{ name = '範疇外問題'; q = '明天台積電股票會漲嗎？' }
)

Write-Host '--- 健康檢查 ---'
try { (Invoke-RestMethod -Uri "$BaseUrl/api/status" -Method GET -TimeoutSec 30) | ConvertTo-Json -Depth 5 } catch { Write-Host $_.Exception.Message }
Write-Host ''

foreach ($t in $tests) {
  Write-Host ("=== " + $t.name + " ===")
  Write-Host ('[Debug] 檢索摘要:')
  $dbg = Invoke-DebugSample -q $t.q -k 5
  $dbg | ConvertTo-Json -Depth 6
  Write-Host ''
  Write-Host ('[Ask] 回答:')
  $resp = Invoke-Ask -q $t.q
  $resp | ConvertTo-Json -Depth 6
  Write-Host ''
}

# Full-stack Button API Test Script
$baseUrl = "http://localhost:8000/api/system"

Write-Host "`n========== 1. LOGIN =========="
$loginBody = '{"username":"admin","password":"admin123"}'
$loginResp = Invoke-RestMethod -Uri "$baseUrl/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResp.data.accessToken
$headers = @{ Authorization = "Bearer $token" }
Write-Host "  [PASS] Login OK"

function Test-Api {
    param([string]$Name, [string]$Method, [string]$Url, [string]$Body = "")
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $headers
            ContentType = "application/json"
        }
        if ($Body -ne "") { $params.Body = $Body }
        $resp = Invoke-RestMethod @params
        $code = $resp.code
        if ($code -eq 0 -or $code -eq 201) {
            Write-Host "  [PASS] $Name (code=$code)"
        } else {
            Write-Host "  [FAIL] $Name (code=$code, msg=$($resp.message))"
        }
        return $resp
    } catch {
        Write-Host "  [ERROR] $Name - $($_.Exception.Message)"
        return $null
    }
}

# ========== 2. USER MANAGEMENT ==========
Write-Host "`n========== 2. USER MANAGEMENT =========="
Test-Api -Name "User List" -Method Post -Url "$baseUrl/user" -Body '{"pageNum":1,"pageSize":10}'

$createResp = Test-Api -Name "Create User" -Method Post -Url "$baseUrl/user/create" -Body '{"username":"testbtn1","password":"Test1234","nickname":"TestBtn","status":1}'
$testUserId = $null
if ($createResp -and $createResp.data -and $createResp.data.id) {
    $testUserId = $createResp.data.id
    Write-Host "    testUserId=$testUserId"
}

if ($testUserId) {
    Test-Api -Name "Update User" -Method Put -Url "$baseUrl/user/$testUserId" -Body '{"nickname":"Updated","status":1}'
    Test-Api -Name "Toggle User Status Off" -Method Put -Url "$baseUrl/user/$testUserId/status" -Body '{"status":0}'
    Test-Api -Name "Toggle User Status On" -Method Put -Url "$baseUrl/user/$testUserId/status" -Body '{"status":1}'
    Test-Api -Name "Reset Password" -Method Put -Url "$baseUrl/user/$testUserId/reset-password" -Body '{"newPassword":"NewPass123"}'
    Test-Api -Name "Assign Role" -Method Post -Url "$baseUrl/user/assign-role" -Body "{`"userId`":`"$testUserId`",`"roleIds`":[`"1`"]}"
    Test-Api -Name "Delete User" -Method Delete -Url "$baseUrl/user/$testUserId"
}

# Batch delete
$u1 = Test-Api -Name "BatchDel-Create1" -Method Post -Url "$baseUrl/user/create" -Body '{"username":"bd1","password":"Test1234","nickname":"BD1","status":1}'
$u2 = Test-Api -Name "BatchDel-Create2" -Method Post -Url "$baseUrl/user/create" -Body '{"username":"bd2","password":"Test1234","nickname":"BD2","status":1}'
$ids = @()
if ($u1 -and $u1.data -and $u1.data.id) { $ids += $u1.data.id }
if ($u2 -and $u2.data -and $u2.data.id) { $ids += $u2.data.id }
if ($ids.Count -gt 0) {
    $batchBody = @{ ids = $ids } | ConvertTo-Json
    Test-Api -Name "Batch Delete Users" -Method Post -Url "$baseUrl/user/batch-delete" -Body $batchBody
}

# ========== 3. ROLE MANAGEMENT ==========
Write-Host "`n========== 3. ROLE MANAGEMENT =========="
Test-Api -Name "Role List" -Method Post -Url "$baseUrl/role" -Body '{"pageNum":1,"pageSize":10}'

$roleResp = Test-Api -Name "Create Role" -Method Post -Url "$baseUrl/role/create" -Body '{"name":"TestBtnRole","code":"test_btn_role","remark":"test"}'
$testRoleId = $null
if ($roleResp -and $roleResp.data -and $roleResp.data.id) {
    $testRoleId = $roleResp.data.id
    Write-Host "    testRoleId=$testRoleId"
}

if ($testRoleId) {
    Test-Api -Name "Update Role" -Method Put -Url "$baseUrl/role/$testRoleId" -Body '{"name":"UpdatedRole","code":"test_btn_role","remark":"updated"}'
    Test-Api -Name "Toggle Role Status Off" -Method Put -Url "$baseUrl/role/$testRoleId/status" -Body '{"status":0}'
    Test-Api -Name "Toggle Role Status On" -Method Put -Url "$baseUrl/role/$testRoleId/status" -Body '{"status":1}'
    Test-Api -Name "Save Role Menu" -Method Post -Url "$baseUrl/role/$testRoleId/menu" -Body '{"menuIds":[]}'
    Test-Api -Name "Delete Role" -Method Delete -Url "$baseUrl/role/$testRoleId"
}

Test-Api -Name "Role Menu IDs" -Method Post -Url "$baseUrl/role-menu-ids" -Body '{"id":"1"}'

# ========== 4. MENU MANAGEMENT ==========
Write-Host "`n========== 4. MENU MANAGEMENT =========="
Test-Api -Name "Menu List" -Method Post -Url "$baseUrl/menu"

$menuResp = Test-Api -Name "Create Menu" -Method Post -Url "$baseUrl/menu/create" -Body '{"title":"TestBtnMenu","menuType":3,"parentId":0,"auths":"test:btn:auth"}'
$testMenuId = $null
if ($menuResp -and $menuResp.data -and $menuResp.data.id) {
    $testMenuId = $menuResp.data.id
    Write-Host "    testMenuId=$testMenuId"
}

if ($testMenuId) {
    Test-Api -Name "Update Menu" -Method Put -Url "$baseUrl/menu/$testMenuId" -Body '{"title":"UpdatedMenu","menuType":3,"parentId":0,"auths":"test:btn:auth2"}'
    
    $childMenuResp = Test-Api -Name "Create Child Menu" -Method Post -Url "$baseUrl/menu/create" -Body "{`"title`":`"ChildMenu`",`"menuType`":3,`"parentId`":`"$testMenuId`",`"auths`":`"test:btn:child`"}"
    $childMenuId = $null
    if ($childMenuResp -and $childMenuResp.data -and $childMenuResp.data.id) {
        $childMenuId = $childMenuResp.data.id
        Test-Api -Name "Delete Child Menu" -Method Delete -Url "$baseUrl/menu/$childMenuId"
    }
    
    Test-Api -Name "Delete Menu" -Method Delete -Url "$baseUrl/menu/$testMenuId"
}

# ========== 5. DEPT MANAGEMENT ==========
Write-Host "`n========== 5. DEPT MANAGEMENT =========="
Test-Api -Name "Dept List" -Method Post -Url "$baseUrl/dept"

$deptResp = Test-Api -Name "Create Dept" -Method Post -Url "$baseUrl/dept/create" -Body '{"name":"TestBtnDept","sort":99,"status":1,"parentId":0}'
$testDeptId = $null
if ($deptResp -and $deptResp.data -and $deptResp.data.id) {
    $testDeptId = $deptResp.data.id
    Write-Host "    testDeptId=$testDeptId"
}

if ($testDeptId) {
    Test-Api -Name "Update Dept" -Method Put -Url "$baseUrl/dept/$testDeptId" -Body '{"name":"UpdatedDept","sort":88,"status":1,"parentId":0}'
    
    $childDeptResp = Test-Api -Name "Create Child Dept" -Method Post -Url "$baseUrl/dept/create" -Body "{`"name`":`"ChildDept`",`"sort`":1,`"status`":1,`"parentId`":`"$testDeptId`"}"
    $childDeptId = $null
    if ($childDeptResp -and $childDeptResp.data -and $childDeptResp.data.id) {
        $childDeptId = $childDeptResp.data.id
        Test-Api -Name "Delete Child Dept" -Method Delete -Url "$baseUrl/dept/$childDeptId"
    }
    
    Test-Api -Name "Delete Dept" -Method Delete -Url "$baseUrl/dept/$testDeptId"
}

# ========== 6. ONLINE USER ==========
Write-Host "`n========== 6. ONLINE USER =========="
Test-Api -Name "Online User List" -Method Post -Url "$baseUrl/online-logs" -Body "{}"
Test-Api -Name "Force Offline" -Method Post -Url "$baseUrl/online-logs/force-offline" -Body "{}"

# ========== 7. LOGS ==========
Write-Host "`n========== 7. LOGS =========="
Test-Api -Name "Login Logs List" -Method Post -Url "$baseUrl/login-logs" -Body '{"pageNum":1,"pageSize":10}'
Test-Api -Name "Login Logs Clear" -Method Post -Url "$baseUrl/login-logs/clear"
Test-Api -Name "Login Logs Batch Delete" -Method Post -Url "$baseUrl/login-logs/batch-delete" -Body '{"ids":[]}'

Test-Api -Name "Operation Logs List" -Method Post -Url "$baseUrl/operation-logs" -Body '{"pageNum":1,"pageSize":10}'
Test-Api -Name "Operation Logs Clear" -Method Post -Url "$baseUrl/operation-logs/clear"

Test-Api -Name "System Logs List" -Method Post -Url "$baseUrl/system-logs" -Body '{"pageNum":1,"pageSize":10}'
Test-Api -Name "System Logs Clear" -Method Post -Url "$baseUrl/system-logs/clear"
Test-Api -Name "System Logs Detail" -Method Post -Url "$baseUrl/system-logs-detail" -Body '{"id":"nonexistent"}'

# ========== 8. ACCOUNT SETTINGS ==========
Write-Host "`n========== 8. ACCOUNT SETTINGS =========="
Test-Api -Name "Get Mine" -Method Get -Url "$baseUrl/mine"
Test-Api -Name "Get Mine Logs" -Method Get -Url "$baseUrl/mine-logs"

Write-Host "`n========== TEST COMPLETE =========="

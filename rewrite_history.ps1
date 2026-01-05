$commits = @(
    @{hash="98ca025d609df17fe35e3b8693154f924ac487df"; date="2026-01-05 12:00:00"; msg="feat: Initial implementation of Crowd Behavior Evaluation System"},
    @{hash="334319a0a5612dbee3c96bbd0ba226b78b3462f0"; date="2026-01-07 12:00:00"; msg="update: Added sample crowd video for testing"},
    @{hash="0dbdc49ce2eeee73729318e30c36e36c92442afc"; date="2026-01-10 12:00:00"; msg="update: Advanced features v2.0 - batch processing, tracking, and analytics"},
    @{hash="354d7719701288fca6cc20a7710001c53e771c4e"; date="2026-01-12 12:00:00"; msg="fix: resolve plotly duplicate ID error and update width parameters"},
    @{hash="62f4024c262c4d9b24160177341cbabae4c0bb37"; date="2026-01-15 12:00:00"; msg="Refactor: Modularize application structure by splitting app.py into components"},
    @{hash="46245666a075c954c0cdcee721ae1794ea678dff"; date="2026-01-17 12:00:00"; msg="Merge remote changes into modular structure (v2.0 integration)"},
    @{hash="fa61b5d43f3cb25e1375adcb65652eb9912067c8"; date="2026-01-20 12:00:00"; msg="refactor: modularize core logic into dedicated modules and enhance visualization"},
    @{hash="197f35a07cb191217b9655a0b2a3601bc608b61a"; date="2026-01-22 12:00:00"; msg="Severity Escalation Implemented"},
    @{hash="a21d809222c25f5fd9d8b59d1f02148686e11efb"; date="2026-01-25 12:00:00"; msg="Added streamlit-drawable-canvas dependency"},
    @{hash="a3decbe7e13844ef4c1794d7320eb6dab98b5bfa"; date="2026-01-28 12:00:00"; msg="Transition to polygon zones and spatial exits configuration"},
    @{hash="d575aad4f2554ce97c51aa77f16a54c449cc6d91"; date="2026-01-31 12:00:00"; msg="Implement polygon density and centroid utilities"},
    @{hash="00629aafe8f7c7f49e17ba1e09f59375efd7081d"; date="2026-02-02 12:00:00"; msg="Support spatial coordinates for exits"},
    @{hash="f2ddace20d86e50c02d4f7064823ff65cea8ec5f"; date="2026-02-05 12:00:00"; msg="Implement dynamic routing to spatial exits"},
    @{hash="0503c342084163ab9091367afc0230f1a441e545"; date="2026-02-07 12:00:00"; msg="Refactor to support string-based zone IDs"},
    @{hash="bccd0c6985d8f37a3d9c6463625461c159f1c076"; date="2026-02-10 12:00:00"; msg="YOLO loading and inference enhancement"},
    @{hash="f1c9bbb8a98765ad5730b17fe051582629259c09"; date="2026-02-12 12:00:00"; msg="Overhaul drawing logic for polygons and overlays"},
    @{hash="e994e496e2808f5167649d89d96b74387d189026"; date="2026-02-15 12:00:00"; msg="Reflect new polygon status reporting in UI"},
    @{hash="a0a74bd8bb3e3c3d1576ea29cbb0b6700cc16e3c"; date="2026-02-18 12:00:00"; msg="Multi-zone drawing support & canvas component integration"},
    @{hash="76c80c96ec07f89f77b9cb5a76e45b53ef2c1b08"; date="2026-02-21 12:00:00"; msg="Consume polygon data structures in main modules"},
    @{hash="e064daf8a3424da50ad076d64abfc9a29cdcacfc"; date="2026-02-24 12:00:00"; msg="Final integration and session state cleanup"}
)

$authorName = "Ashin Saji"
$authorEmail = "ashinsaji2003@gmail.com"

git branch -D main-rewritten 2>$null
git checkout --orphan main-rewritten

for ($i = 0; $i -lt $commits.Length; $i++) {
    $c = $commits[$i]
    Write-Host "Recreating commit $($i+1)/$($commits.Length): $($c.msg)"
    git rm -rf . --quiet
    git checkout $($c.hash) -- .
    git add -A
    $env:GIT_AUTHOR_DATE = $c.date
    $env:GIT_COMMITTER_DATE = $c.date
    git commit -m "$($c.msg)" --author="$authorName <$authorEmail>" --date="$($c.date)" --no-verify --quiet
}

git checkout main
git reset --hard main-rewritten
git branch -D main-rewritten
git checkout HEAD -- rewrite_history.ps1

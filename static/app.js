let waveSurfer = null;
let resultWaveSurfer = null;
let currentFile = null;

document.addEventListener('DOMContentLoaded', () => {
    waveSurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#00adb5',
        progressColor: '#00fff5',
        cursorColor: '#ffffff',
        height: 100,
        responsive: true
    });

    resultWaveSurfer = WaveSurfer.create({
        container: '#waveform-result',
        waveColor: '#28a745',
        progressColor: '#85e39d',
        cursorColor: '#ffffff',
        height: 100,
        responsive: true
    });
});

document.getElementById('audioInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        currentFile = file;
        document.getElementById('track-name').textContent = `トラック: ${file.name}`;
        const url = URL.createObjectURL(file);
        waveSurfer.load(url);
    }
});

document.getElementById('target-lufs')?.addEventListener('input', (e) => {
    document.getElementById('lufs-val').textContent = `${e.target.value} LUFS`;
});

// 進捗表示の制御用関数
function updateProgress(stepIndex, percent, statusMessage) {
    document.getElementById('progress-bar').style.width = `${percent}%`;
    document.getElementById('progress-percent').textContent = `${percent}%`;
    document.getElementById('status-text').textContent = statusMessage;

    // ステータスリストの色を変更
    for (let i = 1; i <= 5; i++) {
        const stepElem = document.getElementById(`step-${i}`);
        if (i < stepIndex) {
            stepElem.style.color = '#28a745'; // 完了: 緑
            stepElem.textContent = stepElem.textContent.replace(/^. /, '✅ ');
        } else if (i === stepIndex) {
            stepElem.style.color = '#00fff5'; // 実行中: シアン (太字)
            stepElem.style.fontWeight = 'bold';
            if (!stepElem.textContent.startsWith('⏳')) {
                stepElem.textContent = '⏳ ' + stepElem.textContent.replace(/^. /, '');
            }
        } else {
            stepElem.style.color = '#8d8d99'; // 待機中: グレー
            stepElem.style.fontWeight = 'normal';
        }
    }
}

async function runProcessing() {
    if (!currentFile) {
        alert('音源ファイルを読み込んでください。');
        return;
    }

    // パネル表示初期化
    const progressCard = document.getElementById('progress-card');
    const resultCard = document.getElementById('result-card');
    progressCard.style.display = 'block';
    resultCard.style.display = 'none';

    // リセット表示
    for (let i = 1; i <= 5; i++) {
        const stepElem = document.getElementById(`step-${i}`);
        stepElem.style.color = '#8d8d99';
        stepElem.style.fontWeight = 'normal';
        stepElem.textContent = stepElem.textContent.replace(/^[✅⏳]\s*/, `${i}. `);
    }

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('declip', document.getElementById('fx-declip')?.checked ?? false);
    formData.append('flute', document.getElementById('fx-flute')?.checked ?? false);
    formData.append('denoise', document.getElementById('fx-denoise')?.checked ?? false);
    formData.append('demask', document.getElementById('fx-demask')?.checked ?? false);
    formData.append('stem', document.getElementById('fx-stem')?.checked ?? false);

    const lufsElem = document.getElementById('target-lufs');
    formData.append('lufs', lufsElem ? lufsElem.value : -14);

    // 擬似プログレスシミュレーション（処理中の視覚フィードバック）
    updateProgress(1, 15, '1. 音割れ補正を実行中...');

    const timer2 = setTimeout(() => updateProgress(2, 35, '2. 笛のバリバリ音をフィルタリング中...'), 800);
    const timer3 = setTimeout(() => updateProgress(3, 55, '3. AIノイズキャンセリング適用中...'), 1800);
    const timer4 = setTimeout(() => updateProgress(4, 75, '4. 中低域のマスキング被りを調整中...'), 2800);
    const timer5 = setTimeout(() => updateProgress(5, 90, '5. ラウドネス最適化 ＆ レンダリング中...'), 3800);

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);
        clearTimeout(timer5);

        if (!response.ok) throw new Error('処理エラーが発生しました。');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // 完了状態にセット
        updateProgress(6, 100, '🎉 すべての自動修復・マスタリングが完了しました！');

        // 全ステップをチェック済みに変更
        for (let i = 1; i <= 5; i++) {
            const stepElem = document.getElementById(`step-${i}`);
            stepElem.style.color = '#28a745';
            stepElem.textContent = stepElem.textContent.replace(/^. /, '✅ ');
        }

        // 1秒後に結果カードを表示して波形を描画
        setTimeout(() => {
            resultCard.style.display = 'block';
            resultWaveSurfer.load(url);
            document.getElementById('downloadBtn').href = url;
        }, 500);

    } catch (err) {
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);
        clearTimeout(timer5);
        document.getElementById('status-text').textContent = '❌ エラー: ' + err.message;
        document.getElementById('status-text').style.color = '#ff4d4d';
    }
}
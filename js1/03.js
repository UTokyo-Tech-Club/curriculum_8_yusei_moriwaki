const N = Number(window.prompt("自然数を入力してください"));

const ans1 = (N*(N+1))/2;

let  ans2 = 0;
for (let i = 1; i <= N; i++) {
    ans2 += i;
}

document.write(ans1 === ans2 ? ans2 : "Failed to compute");
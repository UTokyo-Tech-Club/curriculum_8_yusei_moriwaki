const fibo = (N) => {
    let array = [0, 1];
    for(let i = 2; i <= N; i++){
        array.push(array[i-1] + array[i-2]);
    }
    return array;
}
const fizzBuzz = (array) => {
  return array.map(number => {
    if (number % 3 === 0 && number % 5 === 0) {
      return "FizzBuzz";
    } else if (number % 3 === 0) {
      return "Fizz";
    } else if (number % 5 === 0) {
      return "Buzz";
    } else {
      return number;
    }
  });
};

let range = [];
for (let i = 0; i < 100; i++) {
  range.push(i);
}

console.log(fizzBuzz(range));
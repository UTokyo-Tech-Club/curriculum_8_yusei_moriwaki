import logo from "./logo.svg";
import "./App.css";
import Form from "./Form";
import { useState } from "react";

const ENDPOINT = "https://my-app-firebase-f2402-default-rtdb.firebaseio.com/tweets.json";
const TARGET_NAME = "inada";

function App() {
  const [age, setAge] = useState(null);

  const handleSubmit = async (name, email, formage) => {
    const response = await fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, email, age: formage }),
    });
    console.log("response is ...", response);
  };

  const handleGet = async () => {
    const response = await fetch(ENDPOINT, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const data = await response.json();
    const obj = Object.values(data).find(v => String(v?.name).toLowerCase() === TARGET_NAME);
    setAge(Number(obj.age) + 10);
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
      <Form onSubmit={handleSubmit} />
      <p>年齢: {age ?? "-"}</p>
      <button onClick={handleGet}>年齢を取得</button>
    </div>
  );
}

export default App;


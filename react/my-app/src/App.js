import logo from "./logo.svg";
import "./App.css";
import { useState } from "react";

function App() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [age, setAge] = useState("");

  const handleSubmit = (submit) => {
    submit.preventDefault();
    console.log("onSubmit: ", name, email, age);
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
      <form style={{ display: "flex", flexDirection: "column" }} onSubmit={handleSubmit}>
          <label>Name: </label>
          <input
            type={"text"}
            value={name}
            onChange={(e) => setName(e.target.value)}
          ></input>
          <label>Email: </label>
          <input
            type={"email"}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          ></input>
          <label>Age: </label>
          <input
            type={"number"}
            style={{ marginBottom: 20 }}
            value={age}
            onChange={(e) => setAge(e.target.value)}
          ></input>
          <button type={"submit"}>Submit</button>
        </form>
    </div>
  );
}

export default App;
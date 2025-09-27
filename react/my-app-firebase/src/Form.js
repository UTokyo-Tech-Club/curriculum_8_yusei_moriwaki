import { useState } from "react";

const Form = (props) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [age, setAge] = useState("");

  const submit = (event) => {
    event.preventDefault();
    props.onSubmit(name, email, age);
  }

  return (
    <form style={{ display: "flex", flexDirection: "column" }} onSubmit={submit}>
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
  );
};

export default Form;
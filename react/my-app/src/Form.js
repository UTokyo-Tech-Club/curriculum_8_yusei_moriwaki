import { useState } from "react";

const Form = (props) => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const submit = (event) => {
    event.preventDefault();
    props.onSubmit(name, email);
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
        style={{ marginBottom: 20 }}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      ></input>
      <button type={"submit"}>Submit</button>
    </form>
  );
};

export default Form;
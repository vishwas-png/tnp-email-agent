import { useState, useEffect } from "react";
import NoticeCard from "./NoticeCard";
import "./Dashboard.css";


function Dashboard() {
  const [notices, setNotices] = useState([]);

  useEffect(() => {
    async function fetchNotices() {
      let response = await fetch("http://localhost:8000/notices",{credentials: "include"});
      if(response.status == 401){
        const result=await fetch("http://localhost:8000/refresh-token",{credentials: "include"});
        if(result.ok){
          response=await fetch("http://localhost:8000/notices",{credentials: "include"});
        }

        if (!response.ok) {
            console.log("Failed to load notices — user may need to log in again");
            return;
    }
      }
      const data = await response.json();
      setNotices(data);
      console.log(data[0]);
    }
    fetchNotices();
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="notice-grid">
        {notices.map((notice) => (
          <NoticeCard key={notice.gmail_message_id} notice={notice} />
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
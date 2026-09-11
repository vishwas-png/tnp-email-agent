const categoryColors = {
  internship: "#E1F5EE",
  placement: "#EEEDFE",
  general_notice: "#FAEEDA",
};
function NoticeCard({ notice }) {
   
  return (
    <div className="notice-card" style={{ backgroundColor: categoryColors[notice.category] || "#FAEEDA" }}>
      {notice.category && <span className="tag">{notice.category}</span>}
      <p className="title">{notice.subject}</p>
      {notice.company_name && <p className="company">{notice.company_name}</p>}
      <p className="summary">{notice.summary}</p>
      {notice.deadline && <p className="deadline">Deadline: {new Date(notice.deadline).toLocaleString()}</p>}
    </div>
  );
}

export default NoticeCard;
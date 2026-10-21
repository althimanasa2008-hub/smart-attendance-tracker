"""
Smart Attendance Tracker - Modern Streamlit Web Application

A student dashboard for managing subjects, recording attendance,
visualizing trends, and calculating bunk margins.
"""

import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
import calculator as calc

# ==========================================
# Page Configuration & Theming
# ==========================================
st.set_page_config(
    page_title="Smart Attendance Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Modern, Polished UI (Mobile & Desktop Responsive)
CUSTOM_CSS = """
<style>
    /* Global layout enhancements */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1200px;
    }
    
    /* Header hero styling */
    .hero-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 16px rgba(30, 58, 138, 0.15);
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #E0E7FF;
        margin-top: 0.3rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0.3rem 0;
    }
    .metric-sub {
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Subject Card */
    .subject-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }
    .subject-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E293B;
    }
    .subject-code {
        background: #F1F5F9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        margin-left: 6px;
    }
    
    /* Status Badges */
    .badge-safe {
        background-color: #DCFCE7;
        color: #166534;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-shortage {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-neutral {
        background-color: #F1F5F9;
        color: #475569;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Explanation Box */
    .calc-box {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Database on app load
db.init_db()


# ==========================================
# Sidebar Settings & Navigation
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("Smart Attendance")
    st.caption("Student Attendance & Bunk Tracker")
    st.divider()

    # Load persistent target percentage
    stored_target_str = db.get_setting("target_percentage", default="75.0")
    try:
        current_target = float(stored_target_str)
    except ValueError:
        current_target = 75.0

    st.subheader("⚙️ Target Criteria")
    new_target = st.slider(
        "Minimum Required Attendance (%)",
        min_value=50.0,
        max_value=100.0,
        value=current_target,
        step=1.0,
        help="Standard university minimum attendance is usually 75% or 80%.",
    )
    if new_target != current_target:
        db.set_setting("target_percentage", str(new_target))
        st.toast(f"Target attendance updated to {new_target}%!", icon="✅")
        current_target = new_target

    st.divider()
    nav_option = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📝 Log Attendance",
            "🧮 Bunk Calculator",
            "📚 Manage Subjects",
            "📋 History & Records",
        ],
        index=0,
    )
    st.divider()
    st.caption("💡 Designed for BTech CSE students • SQLite Persistent Storage")


# ==========================================
# Helper Visualization Functions
# ==========================================
def render_donut_gauge(pct: float, target: float):
    """Renders a modern donut chart for overall attendance."""
    color = "#10B981" if pct >= target else ("#EF4444" if pct > 0 else "#94A3B8")
    fig = go.Figure(
        data=[
            go.Pie(
                values=[pct, max(0, 100 - pct)],
                hole=0.72,
                marker_colors=[color, "#E2E8F0"],
                textinfo="none",
                hoverinfo="none",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=180,
        annotations=[
            dict(
                text=f"<b>{pct:.1f}%</b><br><span style='font-size:12px;color:#64748B'>Target {target:.0f}%</span>",
                x=0.5,
                y=0.5,
                font_size=24,
                showarrow=False,
            )
        ],
    )
    return fig


def render_subject_bar_chart(df: pd.DataFrame, target: float):
    """Renders a Plotly horizontal/vertical bar chart comparing subjects to target."""
    df["Color"] = df["percentage"].apply(lambda p: "#10B981" if p >= target else "#EF4444")
    fig = px.bar(
        df,
        x="name",
        y="percentage",
        color="Color",
        color_discrete_map="identity",
        text="percentage",
        labels={"name": "Subject", "percentage": "Attendance %"},
        title="Subject-wise Attendance vs Target",
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
    )
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Target: {target}%",
        annotation_position="top right",
    )
    fig.update_layout(
        yaxis_range=[0, max(105, df["percentage"].max() + 10)],
        xaxis_title="",
        yaxis_title="Percentage (%)",
        margin=dict(t=40, b=20, l=20, r=20),
        height=320,
        showlegend=False,
    )
    return fig


# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if nav_option == "📊 Dashboard":
    # Hero Title Banner
    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title">🎓 Student Attendance Dashboard</h1>
            <p class="hero-subtitle">Real-time attendance tracking, subject insights, and bunk margin analytics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overall = db.get_overall_summary()
    subject_summaries = db.get_subject_summaries()
    metrics = calc.calculate_metrics(overall["attended"], overall["total_classes"], current_target)

    # Top Key Metrics in Columns
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Overall Attendance</div>
                <div class="metric-value" style="color: {'#16A34A' if metrics['status'] == 'on_track' else ('#DC2626' if metrics['total'] > 0 else '#475569')};">
                    {metrics['percentage']:.1f}%
                </div>
                <div class="metric-sub">{metrics['status_badge']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Classes</div>
                <div class="metric-value">{overall['total_classes']}</div>
                <div class="metric-sub">Recorded sessions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Classes Attended</div>
                <div class="metric-value" style="color: #16A34A;">{overall['attended']}</div>
                <div class="metric-sub">Sessions present</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Classes Missed</div>
                <div class="metric-value" style="color: #DC2626;">{overall['missed']}</div>
                <div class="metric-sub">Sessions absent</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # Critical Shortage Alert Banner
    low_attendance_subjects = [s for s in subject_summaries if s["total_classes"] > 0 and s["percentage"] < current_target]
    if low_attendance_subjects:
        shortage_items = []
        for s in low_attendance_subjects:
            s_calc = calc.calculate_metrics(s["attended"], s["total_classes"], current_target)
            to_attend = s_calc["classes_to_attend"]
            shortage_items.append(f"**{s['name']}** ({s['percentage']}%) — Need to attend **{to_attend}** consecutive class{'es' if to_attend and to_attend > 1 else ''}")
        st.error(
            f"⚠️ **Attendance Shortage Alert!** The following subjects are below your {current_target}% target:\n\n"
            + "\n\n".join([f"- {item}" for item in shortage_items])
        )

    # Empty State Check
    if not subject_summaries:
        st.info("👋 Welcome! You haven't added any subjects yet. Head over to **📚 Manage Subjects** to set up your semester curriculum.")
    else:
        # Visual Analytics Section
        col_chart1, col_chart2 = st.columns([1, 1.8])
        with col_chart1:
            st.subheader("🎯 Overall Standing")
            st.plotly_chart(render_donut_gauge(metrics["percentage"], current_target), use_container_width=True)
            st.caption(f"Status: {metrics['message']}")

        with col_chart2:
            st.subheader("📊 Subject Comparison")
            df_subs = pd.DataFrame(subject_summaries)
            active_df = df_subs[df_subs["total_classes"] > 0]
            if not active_df.empty:
                st.plotly_chart(render_subject_bar_chart(active_df, current_target), use_container_width=True)
            else:
                st.info("No attendance records logged yet for charts. Mark some classes to see comparative graphs!")

        st.divider()

        # Subject-wise Detailed Breakdown Cards
        st.subheader("📚 Subject-wise Progress")
        s_cols = st.columns(2)
        for idx, sub in enumerate(subject_summaries):
            col = s_cols[idx % 2]
            with col:
                s_calc = calc.calculate_metrics(sub["attended"], sub["total_classes"], current_target)
                pct = sub["percentage"]
                badge_class = "badge-safe" if pct >= current_target and sub["total_classes"] > 0 else ("badge-shortage" if sub["total_classes"] > 0 else "badge-neutral")
                badge_text = f"🟢 {pct:.1f}% Safe" if pct >= current_target and sub["total_classes"] > 0 else (f"🔴 {pct:.1f}% Shortage" if sub["total_classes"] > 0 else "⚪ No Classes")
                code_badge = f'<span class="subject-code">{sub["code"]}</span>' if sub["code"] else ""

                st.markdown(
                    f"""
                    <div class="subject-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="subject-title">{sub['name']} {code_badge}</span>
                            <span class="{badge_class}">{badge_text}</span>
                        </div>
                        <div style="color: #64748B; font-size: 0.9rem; margin-bottom: 6px;">
                            Attended: <b>{sub['attended']}</b> / {sub['total_classes']} classes &nbsp;|&nbsp; Missed: <b>{sub['missed']}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Progress bar
                prog_value = min(1.0, max(0.0, pct / 100.0))
                st.progress(prog_value)
                st.caption(s_calc["message"])
                st.write("")


# ==========================================
# PAGE 2: LOG ATTENDANCE
# ==========================================
elif nav_option == "📝 Log Attendance":
    st.title("📝 Mark Class Attendance")
    st.caption("Record individual sessions or quickly log attendance for your entire timetable.")

    subjects = db.get_subjects()
    if not subjects:
        st.warning("⚠️ Please add at least one subject in **📚 Manage Subjects** before recording attendance.")
    else:
        tab_single, tab_bulk = st.tabs(["Single Class Log", "⚡ Quick Daily Multi-Log"])

        # Tab 1: Single Session Log
        with tab_single:
            with st.form("single_attendance_form", clear_on_submit=True):
                sub_options = {f"{s['name']}{' (' + s['code'] + ')' if s['code'] else ''}": s["id"] for s in subjects}
                selected_label = st.selectbox("Select Subject", list(sub_options.keys()))
                selected_sub_id = sub_options[selected_label]

                col_date, col_status = st.columns([1, 1])
                with col_date:
                    session_date = st.date_input("Class Date", value=datetime.date.today())
                with col_status:
                    session_status = st.radio("Attendance Status", ["Present", "Absent"], horizontal=True)

                session_remarks = st.text_input("Remarks / Topic Covered (Optional)", placeholder="e.g. Binary Search Trees, Lab 3")

                submitted = st.form_submit_button("💾 Save Attendance Record", use_container_width=True, type="primary")
                if submitted:
                    ok, msg = db.record_attendance(
                        subject_id=selected_sub_id,
                        date_str=str(session_date),
                        status=session_status,
                        remarks=session_remarks,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

        # Tab 2: Quick Multi-Subject Log (Log all classes for a date in one click)
        with tab_bulk:
            st.write("Quickly mark attendance for all your subjects for a specific day:")
            bulk_date = st.date_input("Select Date for Daily Log", value=datetime.date.today(), key="bulk_date")

            bulk_status_map = {}
            st.write("---")
            for sub in subjects:
                c_name, c_choice = st.columns([2, 1])
                with c_name:
                    code_disp = f"`{sub['code']}`" if sub["code"] else ""
                    st.markdown(f"**{sub['name']}** {code_disp}")
                with c_choice:
                    bulk_status_map[sub["id"]] = st.radio(
                        f"Status for {sub['name']}",
                        ["Present", "Absent", "Skip (No Class)"],
                        index=0,
                        key=f"bulk_{sub['id']}",
                        horizontal=True,
                        label_visibility="collapsed",
                    )

            if st.button("🚀 Submit Daily Attendance", use_container_width=True, type="primary"):
                saved_count = 0
                dup_count = 0
                for sub_id, choice in bulk_status_map.items():
                    if choice in ("Present", "Absent"):
                        ok, _ = db.record_attendance(
                            subject_id=sub_id,
                            date_str=str(bulk_date),
                            status=choice,
                            remarks="Batch recorded",
                        )
                        if ok:
                            saved_count += 1
                        else:
                            dup_count += 1

                if saved_count > 0:
                    st.success(f"✅ Successfully recorded attendance for {saved_count} subject(s) on {bulk_date}.")
                if dup_count > 0:
                    st.warning(f"ℹ️ {dup_count} subject(s) already had records for {bulk_date} and were skipped.")


# ==========================================
# PAGE 3: SMART BUNK CALCULATOR
# ==========================================
elif nav_option == "🧮 Bunk Calculator":
    st.title("🧮 Smart Attendance & Bunk Calculator")
    st.caption("Plan your leaves, prevent attendance shortages, and simulate future scenarios.")

    subject_summaries = db.get_subject_summaries()
    overall = db.get_overall_summary()

    # Calculator scope options: Overall or Specific Subject
    options = {"Overall Attendance": {"attended": overall["attended"], "total": overall["total_classes"], "name": "Overall"}}
    for s in subject_summaries:
        options[f"{s['name']}{' (' + s['code'] + ')' if s['code'] else ''}"] = {
            "attended": s["attended"],
            "total": s["total_classes"],
            "name": s["name"],
        }

    selected_scope = st.selectbox("Select Attendance Scope", list(options.keys()))
    scope_data = options[selected_scope]

    # Target percentage slider for calculator
    calc_target = st.slider("Target Attendance Percentage (%)", 50.0, 100.0, float(current_target), 1.0, key="calc_target_slider")

    # Compute metrics using the formula
    res = calc.calculate_metrics(scope_data["attended"], scope_data["total"], calc_target)

    st.write("")
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Current Attendance", f"{res['percentage']:.1f}%", f"{res['percentage'] - calc_target:+.1f}% vs Target")
    with col_stat2:
        st.metric("Classes Held / Attended", f"{res['attended']} / {res['total']}")
    with col_stat3:
        st.metric("Classes Missed", f"{res['missed']}")

    # Results & Advice
    st.write("")
    if res["status"] == "no_data":
        st.info("ℹ️ No classes have been held yet in this scope. Attendance calculations will appear once classes are logged.")
    elif res["status"] == "on_track":
        st.success(
            f"### 🎉 Safe Zone!\n\n"
            f"- Your current attendance is **{res['percentage']:.1f}%**, which is above your target of **{calc_target:.1f}%**.\n"
            f"- You can safely miss (bunk) the next **{res['classes_can_miss']}** class(es) in a row while staying at or above **{calc_target:.1f}%**.\n"
            f"- Missing **{res['classes_can_miss'] + 1}** classes would drop you below your minimum target."
        )
    elif res["is_target_impossible"]:
        st.error(
            f"### ⚠️ Impossible Target\n\n"
            f"Your target is **100%**, but you have already missed **{res['missed']}** class(es). "
            f"Even if you attend every upcoming class for the rest of your life, attendance will asymptotically approach but never reach 100%."
        )
    else:
        st.error(
            f"### 🚨 Shortage Detected!\n\n"
            f"- Your current attendance is **{res['percentage']:.1f}%**, which is below your target of **{calc_target:.1f}%**.\n"
            f"- You must attend the next **{res['classes_to_attend']}** consecutive class(es) without taking any leave to reach **{calc_target:.1f}%**."
        )

    # Detailed Step-by-Step Formula Breakdown (Great for BTech learning!)
    with st.expander("📖 View Mathematical Formula & Step-by-Step Proof"):
        st.markdown(
            r"""
            ### Mathematical Derivation

            Let:
            - $P$ = Total classes attended (**Present**)
            - $T$ = Total classes conducted
            - $C$ = Target attendance percentage (e.g. $75\%$)

            ---

            #### 1. Consecutive Classes to Attend to Reach Target ($x$)
            If current attendance is below target ($\frac{P}{T} < \frac{C}{100}$), we solve for the minimum future consecutive classes $x$ you must attend:
            $$\frac{P + x}{T + x} \ge \frac{C}{100}$$
            $$100(P + x) \ge C(T + x)$$
            $$100P + 100x \ge CT + Cx$$
            $$x(100 - C) \ge CT - 100P$$
            $$x = \left\lceil \frac{C \cdot T - 100 \cdot P}{100 - C} \right\rceil$$

            ---

            #### 2. Classes You Can Safely Miss / Bunk ($y$)
            If current attendance is at or above target ($\frac{P}{T} \ge \frac{C}{100}$), we solve for the maximum future classes $y$ you can skip without falling below $C$:
            $$\frac{P}{T + y} \ge \frac{C}{100}$$
            $$100 \cdot P \ge C(T + y)$$
            $$C \cdot y \le 100 \cdot P - C \cdot T$$
            $$y = \left\lfloor \frac{100 \cdot P - C \cdot T}{C} \right\rfloor$$
            """
        )

    # What-If Simulator
    st.divider()
    st.subheader("🔮 What-If Simulator")
    st.caption("Experiment with future scenarios to see how attending or missing future classes impacts your score.")
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        fut_attend = st.number_input("Hypothetical future classes attended", min_value=0, max_value=100, value=5, step=1)
    with sim_col2:
        fut_miss = st.number_input("Hypothetical future classes missed", min_value=0, max_value=100, value=1, step=1)

    sim_res = calc.simulate_future_attendance(scope_data["attended"], scope_data["total"], fut_attend, fut_miss)
    sim_status = "🟢 Above Target" if sim_res["new_percentage"] >= calc_target else "🔴 Below Target"

    st.markdown(
        f"""
        <div class="calc-box">
            <h4>Projected Result:</h4>
            <ul>
                <li>New Attended: <b>{sim_res['new_attended']}</b> / {sim_res['new_total']} classes</li>
                <li>Projected Attendance: <b>{sim_res['new_percentage']:.2f}%</b> ({sim_res['difference']:+.2f}% change)</li>
                <li>Status: <b>{sim_status}</b></li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# PAGE 4: MANAGE SUBJECTS
# ==========================================
elif nav_option == "📚 Manage Subjects":
    st.title("📚 Curriculum & Subject Management")
    st.caption("Add your semester courses, edit subject codes, or delete courses.")

    tab_list, tab_add, tab_edit = st.tabs(["Current Subjects", "➕ Add New Subject", "✏️ Edit / Delete Subject"])

    # Tab 1: Current Subjects Table
    with tab_list:
        subjects = db.get_subjects()
        if not subjects:
            st.info("No subjects added yet. Click on **➕ Add New Subject** to add your first course.")
        else:
            df = pd.DataFrame(subjects)
            df.rename(columns={"name": "Subject Name", "code": "Subject Code", "created_at": "Added On"}, inplace=True)
            st.dataframe(df[["id", "Subject Name", "Subject Code", "Added On"]], use_container_width=True, hide_index=True)

    # Tab 2: Add Subject Form
    with tab_add:
        with st.form("add_subject_form", clear_on_submit=True):
            st.subheader("Add a New Subject")
            name_input = st.text_input("Subject Name *", placeholder="e.g. Data Structures & Algorithms")
            code_input = st.text_input("Subject Code (Optional)", placeholder="e.g. CS201")
            submitted = st.form_submit_button("➕ Add Subject", use_container_width=True, type="primary")

            if submitted:
                ok, msg = db.add_subject(name_input, code_input)
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # Tab 3: Edit or Delete
    with tab_edit:
        subjects = db.get_subjects()
        if not subjects:
            st.info("No subjects available to edit.")
        else:
            sub_dict = {f"{s['name']}{' (' + s['code'] + ')' if s['code'] else ''}": s for s in subjects}
            selected_label = st.selectbox("Select Subject to Modify", list(sub_dict.keys()))
            selected_sub = sub_dict[selected_label]

            col_edit, col_del = st.columns(2)
            with col_edit:
                st.subheader("✏️ Edit Subject Details")
                with st.form("edit_form"):
                    updated_name = st.text_input("Subject Name", value=selected_sub["name"])
                    updated_code = st.text_input("Subject Code", value=selected_sub["code"])
                    save_edit = st.form_submit_button("Update Subject", use_container_width=True)
                    if save_edit:
                        ok, msg = db.update_subject(selected_sub["id"], updated_name, updated_code)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            with col_del:
                st.subheader("🗑️ Delete Subject")
                st.warning("⚠️ Deleting a subject will permanently remove all associated attendance logs.")
                confirm = st.checkbox(f"Yes, delete '{selected_sub['name']}' and its records")
                if st.button("Delete Subject", type="secondary", disabled=not confirm, use_container_width=True):
                    ok, msg = db.delete_subject(selected_sub["id"])
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


# ==========================================
# PAGE 5: HISTORY & RECORDS
# ==========================================
elif nav_option == "📋 History & Records":
    st.title("📋 Attendance Logs & Export")
    st.caption("Filter records, correct mistakes, and export your data as CSV.")

    subjects = db.get_subjects()
    if not subjects:
        st.info("No subjects found. Please add subjects first.")
    else:
        # Filter controls
        f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1])
        with f_col1:
            filter_sub_options = {"All Subjects": None}
            for s in subjects:
                filter_sub_options[s["name"]] = s["id"]
            selected_filter_label = st.selectbox("Filter by Subject", list(filter_sub_options.keys()))
            filter_sub_id = filter_sub_options[selected_filter_label]

        with f_col2:
            filter_status = st.selectbox("Filter by Status", ["All", "Present", "Absent"])
            status_param = None if filter_status == "All" else filter_status

        with f_col3:
            st.write("")
            st.write("")
            # Reset button
            if st.button("Clear Filters", use_container_width=True):
                st.rerun()

        # Fetch records
        records = db.get_attendance_history(subject_id=filter_sub_id, status=status_param)

        if not records:
            st.info("No attendance records match the selected filter criteria.")
        else:
            df_records = pd.DataFrame(records)
            df_records.rename(
                columns={
                    "id": "Record ID",
                    "subject_name": "Subject",
                    "subject_code": "Code",
                    "date": "Date",
                    "status": "Status",
                    "remarks": "Remarks",
                },
                inplace=True,
            )

            # Export to CSV
            csv_data = df_records[["Record ID", "Subject", "Code", "Date", "Status", "Remarks"]].to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Filtered Logs to CSV",
                data=csv_data,
                file_name=f"attendance_records_{datetime.date.today()}.csv",
                mime="text/csv",
                help="Download your attendance history to open in Microsoft Excel or Google Sheets.",
            )

            st.dataframe(
                df_records[["Record ID", "Subject", "Code", "Date", "Status", "Remarks"]],
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            # Record Correction / Deletion Tool
            st.subheader("🛠️ Correct or Remove an Entry")
            record_options = {
                f"ID {r['id']} - {r['subject_name']} ({r['date']}) [{r['status']}]": r for r in records
            }
            selected_rec_label = st.selectbox("Select Record to Modify", list(record_options.keys()))
            selected_rec = record_options[selected_rec_label]

            m_col1, m_col2 = st.columns(2)
            with m_col1:
                with st.form("edit_record_form"):
                    st.write("**Edit Status & Remarks**")
                    new_status = st.radio("Correct Status", ["Present", "Absent"], index=0 if selected_rec["status"] == "Present" else 1, horizontal=True)
                    new_remarks = st.text_input("Update Remarks", value=selected_rec["remarks"] or "")
                    if st.form_submit_button("Save Corrections", use_container_width=True):
                        ok, msg = db.update_attendance_record(selected_rec["id"], new_status, new_remarks)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            with m_col2:
                st.write("**Delete Record**")
                st.caption("Remove this session log permanently from the database.")
                if st.button("🗑️ Delete Selected Record", type="secondary", use_container_width=True):
                    ok, msg = db.delete_attendance_record(selected_rec["id"])
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

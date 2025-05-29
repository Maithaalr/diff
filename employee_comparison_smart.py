
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="مقارنة بيانات الموظفين", layout="wide")

st.image("logo.png", width=250)
st.title("مقارنة مرنة بين ملفي بيانات الموظفين")

old_file = st.file_uploader(" ارفع ملف البيانات القديمة", type=["xlsx", "csv"])
new_file = st.file_uploader(" ارفع ملف البيانات الجديدة", type=["xlsx", "csv"])

if old_file and new_file:
    if old_file.name.endswith(".csv"):
        old_df = pd.read_csv(old_file)
    else:
        old_df = pd.read_excel(old_file)

    if new_file.name.endswith(".csv"):
        new_df = pd.read_csv(new_file)
    else:
        new_df = pd.read_excel(new_file)

    st.success(" تم تحميل الملفين")

    id_column = None
    for col in old_df.columns:
        if 'الرقم' in col and 'وظيفي' in col:
            id_column = col
            break

    if not id_column:
        st.error(" لم يتم العثور على عمود الرقم الوظيفي. يرجى التأكد من وجوده.")
        st.stop()

    st.info(f"                        ")

    # بدون حذف المسافات
    old_cleaned = old_df.copy()
    new_cleaned = new_df.copy()

    shared_cols = list(set(old_df.columns).intersection(set(new_df.columns)))
    shared_cols = [col for col in shared_cols if col != id_column and 'تاريخ التعيين' not in col]

    merged = pd.merge(old_cleaned, new_cleaned, on=id_column, suffixes=('_old', '_new'), how='outer', indicator=True)

    differences = []
    changed_employee_ids = set()

    for col in shared_cols:
        col_old = col + "_old"
        col_new = col + "_new"
        if col_old in merged.columns and col_new in merged.columns:
            both_mask = merged["_merge"] == "both"
            compare = merged.loc[both_mask]
            if col == "الوحدة التنظيمية":
            # إزالة أول ثلاث حروف من القيمة الجديدة فقط للوحدة التنظيمية
                compare[col_old] = compare[col_old].astype(str).str.strip()
                compare[col_new] = compare[col_new].astype(str).str[3:].str.strip()
            diff_mask = compare[col_old] != compare[col_new]

            if diff_mask.any():
                diff_rows = compare[diff_mask][[id_column, col_old, col_new]].copy()
                diff_rows.rename(columns={col_old: "القيمة القديمة", col_new: "القيمة الجديدة"}, inplace=True)
                diff_rows["اسم العمود"] = col
                differences.append(diff_rows[[id_column, "اسم العمود", "القيمة القديمة", "القيمة الجديدة"]])
                changed_employee_ids.update(diff_rows[id_column].unique())

    new_only = merged[merged["_merge"] == "right_only"]
    new_employees_count = new_only[id_column].nunique()

    tab1, tab2, tab3, tab4 = st.tabs(["الاختلافات", "الموظفين الجدد", "رسم بياني", "فلترة"])


    with tab1:
        if differences:
            final_df = pd.concat(differences, ignore_index=True)

            st.subheader(" اختلافات في البيانات:")
            st.dataframe(final_df, use_container_width=True)

            st.markdown(f"عدد الموظفين اللتي تغيرت بياناتهم: `{len(changed_employee_ids)}`")

            csv_data = final_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(" تحميل النتائج", data=csv_data, file_name="التغير.csv", mime="text/csv")
        else:
            st.success(" لا توجد اختلافات في البيانات.")

    with tab2:
        st.subheader(":الموظفون الجدد")
        if not new_only.empty:
            new_rows = new_df[new_df[id_column].isin(new_only[id_column])]
            st.dataframe(new_rows, use_container_width=True)

            new_csv = new_rows.to_csv(index=False).encode("utf-8-sig")
            st.download_button(" تحميل ملف للموظفين الجدد", data=new_csv, file_name="الموظفين_الجدد.csv", mime="text/csv")
        else:
            st.info("لا توجد سجلات جديدة.")

    with tab3:
        if differences:
            chart_df = pd.concat(differences)["اسم العمود"].value_counts().reset_index()
            chart_df.columns = ["العامود", "عدد التغييرات"]
            fig = px.bar(chart_df, x="العامود", y="عدد التغييرات", color="العامود", color_discrete_sequence=px.colors.sequential.Blues)
            st.subheader(" عدد التغييرات حسب العامود:")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد تغييرات في العامود لعرضها.")

    with tab4:
        st.subheader(" فلترة التغييرات حسب العمود والقيمة")

        if not final_df.empty:
           selected_col = st.selectbox("اختاري العمود:", sorted(final_df["اسم العمود"].unique()))
           filtered_values = final_df[final_df["اسم العمود"] == selected_col]["القيمة القديمة"].dropna().unique().tolist()
           selected_value = st.selectbox("اختاري القيمة القديمة:", ["الكل"] + sorted(filtered_values))

           filtered_df = final_df[final_df["اسم العمود"] == selected_col]
           if selected_value != "الكل":
                filtered_df = filtered_df[filtered_df["القيمة القديمة"] == selected_value]

           st.dataframe(filtered_df, use_container_width=True)
           st.success(f"عدد الصفوف المطابقة: {len(filtered_df)}")

           csv_data_filt = filtered_df.to_csv(index=False).encode("utf-8-sig")
           st.download_button(" تحميل النتائج", data=csv_data_filt, file_name="التغير_لعامود_معين.csv", mime="text/csv")

        else:
            st.info("لا توجد تغييرات لعرضها.")

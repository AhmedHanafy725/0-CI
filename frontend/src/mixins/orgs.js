export const orgs = {
    methods: {
        getStatus(status) {
            if (status == "error") return "kt-bg-error";
            else if (status == "failure") return "kt-bg-failure";
            else if (status == "success") return "kt-bg-success";
            else return "orange";
        }
    },
}
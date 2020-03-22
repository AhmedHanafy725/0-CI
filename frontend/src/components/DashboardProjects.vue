<template>
  <!--begin:: Widgets/Inbound Bandwidth-->
  <div
    class="kt-portlet kt-portlet--fit kt-portlet--head-noborder kt-portlet--height-fluid-half"
    @click="selectedId(id)"
  >
    <div class="kt-portlet__head kt-portlet__space-x">
      <div class="kt-portlet__head-label">
        <h3 class="kt-portlet__head-title">{{ project }}</h3>
      </div>
    </div>
    <div class="kt-portlet__body kt-portlet__body--fluid">
      <div class="kt-widget20">
        <div class="kt-widget20__content kt-portlet__space-x">
          <span
            class="kt-widget20__number text-capitalize"
            :class="{
            'kt-font-success': status == 'success',
            'kt-font-error': status == 'error',
            'kt-font-failure': status == 'failure'}"
          >{{ status }}</span>
          <span class="kt-widget20__desc text-right">{{ time }}</span>
        </div>
      </div>
    </div>
  </div>
  <!--end:: Widgets/Inbound Bandwidth-->
</template>

<script>
import axios from "axios";
export default {
  name: "DashboardProjects",
  props: ["project"],
  data() {
    return {
      projects: null,
      timestamp: null,
      status: null,
      id: null
    };
  },
  methods: {
    getData() {
      const path = process.env.VUE_APP_BASE_URL + `projects/${this.project}`;
      axios.get(path).then(response => {
        this.projects = response.data;
        this.filteredItems = this.projects.filter(
          item => item.status !== "pending"
        );
        this.timestamp = this.filteredItems[0].timestamp;
        this.status = this.filteredItems[0].status;
        this.id = this.filteredItems[0].id;
      });
    },
    selectedId(event) {
      this.$emit("childToParent", event);
    }
  },
  computed: {
    time() {
      var d = new Date();
      var nowTs = Math.floor(d.getTime() / 1000);
      var seconds = nowTs - this.timestamp;

      // more that two days
      if (seconds > 2 * 24 * 3600) {
        return "a few days ago";
      }
      // a day
      if (seconds > 24 * 3600) {
        return "yesterday";
      }

      if (seconds > 3600) {
        return "a few hours ago";
      }
      if (seconds > 1800) {
        return "Half an hour ago";
      }
      if (seconds > 60) {
        return Math.floor(seconds / 60) + " minutes ago";
      }
    }
  },
  created() {
    this.getData();
  }
};
</script>

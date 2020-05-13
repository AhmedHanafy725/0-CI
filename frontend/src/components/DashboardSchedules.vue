<template>
  <!--begin:: Widgets/Inbound Bandwidth-->
  <div
    class="kt-portlet kt-portlet--fit kt-portlet--head-noborder kt-portlet--height-fluid-half mb-0"
    @click="selectedId(id)"
  >
    <div class="kt-portlet__head kt-portlet__space-x">
      <div class="kt-portlet__head-label">
        <h3 class="kt-portlet__head-title">{{ schedule }}</h3>
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
import EventService from "../services/EventService";
export default {
  name: "DashboardSchedules",
  props: ["schedule"],
  data() {
    return {
      filteredItems: [],
      status: null,
      timestamp: null,
      id: null
    };
  },
  methods: {
    getSchedules() {
      EventService.getSchedulesDetails(this.schedule)
        .then(response => {
          if (response.data.length > 0) {
            this.filteredItems = response.data.filter(
              item => item.status !== "pending"
            );
            this.timestamp = this.filteredItems[0].timestamp;
            this.status = this.filteredItems[0].status;
            this.id = this.filteredItems[0].id;
          } else {
            state.visibility = false;
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
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
      if (seconds < 60) {
        return "Now";
      }
    }
  },
  created() {
    this.getSchedules();
  }
};
</script>

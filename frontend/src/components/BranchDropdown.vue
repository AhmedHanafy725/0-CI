<template>
  <div class="kt-portlet__head-toolbar">
    <a
      href="#"
      class="btn btn-label-success btn-sm btn-bold dropdown-toggle"
      data-toggle="dropdown"
    >Branches</a>
    <div class="dropdown-menu dropdown-menu-fit dropdown-menu-right">
      <ul class="kt-nav">
        <li class="kt-nav__item text-center" v-if="spinner">
          <div class="kt-spinner kt-spinner--sm kt-spinner--brand"></div>
        </li>
        <li class="kt-nav__item" v-for="existedBranch in existedBranches" :key="existedBranch.id">
          <a href="#" class="kt-nav__link">
            <span
              class="kt-nav__link-text"
              @click.self="selectedBranch(existedBranch)"
            >{{ existedBranch }}</span>
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "BranchDropdown",
  props: ["repo"],
  data() {
    return {
      spinner: true,
      existedBranches: null
    };
  },
  methods: {
    getExistedBranches() {
      EventService.getBranches(this.repo)
        .then(response => {
          this.spinner = false;
          this.existedBranches = response.data.exist;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    selectedBranch(event) {
      this.$emit("childToParent", event);
    }
  },
  created() {
    this.getExistedBranches();
  }
};
</script>

<style scoped>
.dropdown-menu-right {
  z-index: 999;
}
ul {
  padding-left: 0;
}
.kt-nav {
  min-height: 50px;
}

.kt-nav .kt-spinner {
  width: 15%;
  margin: 20px auto;
  text-align: center;
}
</style>

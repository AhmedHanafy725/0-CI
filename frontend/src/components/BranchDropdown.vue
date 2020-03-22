<template>
  <div class="kt-portlet__head-toolbar">
    <a
      href="#"
      class="btn btn-label-success btn-sm btn-bold dropdown-toggle"
      data-toggle="dropdown"
    >Branches</a>
    <div class="dropdown-menu dropdown-menu-fit dropdown-menu-right">
      <ul class="kt-nav">
        <li class="kt-nav__item" v-for="(existedBranch, i) in existedBranches" :key="i">
          <a href="#" class="kt-nav__link">
            <span
              class="kt-nav__link-text"
              @click="selectedBranch(existedBranch)"
            >{{ existedBranch }}</span>
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Axios from "axios";
export default {
  name: "BranchDropdown",
  props: ["repo"],
  data() {
    return {
      existedBranches: null
    };
  },
  methods: {
    getBranches() {
      const path = process.env.VUE_APP_BASE_URL + `repos/${this.repo}`;
      Axios.get(path)
        .then(response => {
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
    this.getBranches();
  }
};
</script>

<style scoped>
.dropdown-menu-right {
  z-index: 999;
}
</style>

<template>
  <li
    class="kt-menu__item kt-menu__item--submenu"
    aria-haspopup="true"
    data-ktmenu-submenu-toggle="hover"
  >
    <a href="javascript:;" class="kt-menu__link kt-menu__toggle">
      <span class="kt-menu__link-text">{{ repoName }}</span>
      <i class="kt-menu__ver-arrow la la-angle-right"></i>
    </a>
    <div class="kt-menu__submenu">
      <span class="kt-menu__arrow"></span>
      <ul class="kt-menu__subnav">
        <li class="kt-menu__item kt-menu__item--parent" aria-haspopup="true">
          <span class="kt-menu__link">
            <span class="kt-menu__link-text">Subheaders</span>
          </span>
        </li>
        <li class="kt-menu__section">
          <h4 class="kt-menu__section-text">Existed</h4>
          <i class="kt-menu__section-icon flaticon-more-v2"></i>
        </li>
        <li
          class="kt-menu__item"
          aria-haspopup="true"
          v-for="(existedBranch, index) in existedBranches"
          :key="index"
        >
          <router-link
            :to="branchLink +  existedBranch"
            class="kt-menu__link"
            :title="existedBranch"
          >
            <i class="kt-menu__link-bullet kt-menu__link-bullet--dot">
              <span></span>
            </i>
            <span class="kt-menu__link-text">{{ existedBranch }}</span>
          </router-link>
        </li>
        <li class="kt-menu__section">
          <h4 class="kt-menu__section-text">Deleted</h4>
          <i class="kt-menu__section-icon flaticon-more-v2"></i>
        </li>
        <li
          class="kt-menu__item"
          aria-haspopup="true"
          v-for="(deletedBranch, i) in deletedBranches"
          :key="i + 'a'"
        >
          <router-link
            :to="branchLink +  deletedBranch"
            class="kt-menu__link"
            :title="deletedBranch"
          >
            <i class="kt-menu__link-bullet kt-menu__link-bullet--dot">
              <span></span>
            </i>
            <span class="kt-menu__link-text">{{ deletedBranch }}</span>
          </router-link>
        </li>
      </ul>
    </div>
  </li>
</template>
<script>
import axios from "axios";
export default {
  name: "AsideRepos",
  props: ["repo", "orgName", "branch"],
  data() {
    return {
      existedBranches: null,
      deletedBranches: null
    };
  },
  computed: {
    repoName: function() {
      return this.repo.substring(this.repo.indexOf("/") + 1);
    },
    branchLink: function() {
      return "/repos/" + this.repo + "?branch=";
    }
  },
  methods: {
    getBranches() {
      const path = process.env.VUE_APP_BASE_URL + `repos/${this.repo}`;
      axios
        .get(path)
        .then(response => {
          this.existedBranches = response.data.exist;
          this.deletedBranches = response.data.deleted;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    }
  },
  created() {
    this.getBranches();
  }
};
</script>

<style scoped>
.kt-aside-menu
  .kt-menu__nav
  > .kt-menu__item
  .kt-menu__submenu
  .kt-menu__section {
  margin: 0;
}
</style>

<template>
  <li
    class="kt-menu__item kt-menu__item--submenu"
    :class="{
      'kt-menu__item--open': show,
      '': !show,
    }"
    aria-haspopup="true"
    data-ktmenu-submenu-toggle="hover"
    v-if="existedBranches"
  >
    <a href="javascript:;" class="kt-menu__link kt-menu__toggle" @click="toggle()">
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
          v-for="existedBranch in existedBranches"
          :key="existedBranch.id"
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
          v-for="deletedBranch in deletedBranches"
          :key="deletedBranch.id"
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
import EventService from "../services/EventService";
export default {
  name: "AsideRepos",
  props: ["repo"],
  data() {
    return {
      show: false,
      existedBranches: null,
      deletedBranches: null
    };
  },
  methods: {
    fetchBranches() {
      EventService.getBranches(this.repo)
        .then(response => {
          this.existedBranches = response.data.exist;
          this.deletedBranches = response.data.deleted;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    toggle() {
      this.show = !this.show;
    }
  },
  computed: {
    repoName: function() {
      return this.repo.substring(this.repo.indexOf("/") + 1);
    },
    branchLink: function() {
      return "/repos/" + this.repo + "?branch=";
    }
  },
  created() {
    this.fetchBranches();
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

.show {
  display: block !important;
}
</style>

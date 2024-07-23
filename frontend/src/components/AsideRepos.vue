<template>
  <li
    class="kt-menu__item kt-menu__item--submenu"
    aria-haspopup="true"
    data-ktmenu-submenu-toggle="hover"
  >
    <a href="javascript:;" class="kt-menu__link kt-menu__toggle">
      <span class="kt-menu__link-text">{{ formatName }}</span>
      <i class="kt-menu__ver-arrow la la-angle-right"></i>
    </a>
    <div class="kt-menu__submenu">
      <span class="kt-menu__arrow"></span>
      <ul class="kt-menu__subnav">
        <li class="kt-menu__item kt-menu__item--parent" aria-haspopup="true">
          <span class="kt-menu__link">
            <span class="kt-menu__link-text">{{ formatName }}</span>
          </span>
        </li>

        <li class="kt-menu__section" v-if="existedBranches.length > 0">
          <h4 class="kt-menu__section-text">Existed</h4>
          <i class="kt-menu__section-icon flaticon-more-v2"></i>
        </li>

        <li
          class="kt-menu__item"
          aria-haspopup="true"
          v-for="(existedBranch, index) in existedBranches"
          :key="existedBranch"
          :class="{ 'kt-menu__item--active': activeIndex === index}"
          @click="setActive(index)"
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

        <li class="kt-menu__section" v-if="deletedBranches.length > 0">
          <h4 class="kt-menu__section-text">Deleted</h4>
          <i class="kt-menu__section-icon flaticon-more-v2"></i>
        </li>

        <li
          class="kt-menu__item"
          aria-haspopup="true"
          v-for="(deletedBranch, index) in deletedBranches"
          :key="deletedBranch"
          :class="{ 'kt-menu__item--active': activeIndex === index}"
          @click="setActive(index)"
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
      existedBranches: "",
      deletedBranches: "",
      activeIndex: undefined
    };
  },
  computed: {
    formatName() {
      return this.repo.substring(this.repo.indexOf("/") + 1);
    },
    repoName: function() {
      return this.repo.substring(this.repo.indexOf("/") + 1);
    },
    branchLink: function() {
      return "/repos/" + this.repo + "/";
    }
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
    setActive(index) {
      this.activeIndex = index;
    }
  },
  created() {
    this.fetchBranches();
  }
};
</script>

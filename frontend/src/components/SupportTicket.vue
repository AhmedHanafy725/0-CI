<template>
  <!--begin:: Widgets/Support Tickets -->
  <div class="kt-portlet kt-portlet--height-fluid">
    <div class="kt-portlet__head">
      <div class="kt-portlet__head-label">
        <h3 class="kt-portlet__head-title">{{ title }}</h3>
      </div>
      <div class="kt-portlet__head-toolbar">
        <button type="button" class="btn btn-success btn-sm" @click="newIssue()">New issue</button>
      </div>
    </div>
    <div class="kt-portlet__body">
      <div class="kt-widget3">
        <div class="kt-widget3__item" v-for="issue in issues.slice(0, 5)" :key="issue.id">
          <div class="kt-widget3__header">
            <div class="kt-widget3__user-img">
              <img class="kt-widget3__img" :src="issue.user.avatar_url" alt />
            </div>
            <div class="kt-widget3__info">
              <a
                :href="issue.user.html_url"
                target="_blank"
                class="kt-widget3__username"
              >{{ issue.user.login }}</a>
              <br />
              <span class="kt-widget3__time">{{ issue.created_at }}</span>
            </div>
            <span class="kt-widget3__status kt-font-info">{{ issue.state }}</span>
          </div>
          <div class="kt-widget3__body">
            <p class="kt-widget3__text">{{ issue.title }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!--end:: Widgets/Support Tickets -->
</template>

<script>
import axios from "axios";
export default {
  name: "SupportTicket",
  data() {
    return {
      title: "Support Tickets",
      owner: "threefoldtech",
      repo: "zeroCI",
      issues: null
    };
  },
  methods: {
    getIssues() {
      const path = `https://api.github.com/repos/${this.owner}/${this.repo}/issues`;
      axios
        .get(path)
        .then(response => {
          this.issues = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    newIssue() {
      window.open(`https://github.com/${this.owner}/${this.repo}/issues/new`);
    }
  },
  created() {
    this.getIssues();
  }
};
</script>

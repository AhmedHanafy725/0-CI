<template>
  <!-- begin:: Content -->
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <div class="kt-portlet kt-portlet--mobile">
      <div class="kt-portlet__head kt-portlet__head--lg">
        <div class="kt-portlet__head-label">
          <span class="kt-portlet__head-icon">
            <i class="kt-font-brand flaticon2-line-chart"></i>
          </span>
          <h3 class="kt-portlet__head-title">{{ repoName }}/{{ $route.query.branch }}</h3>
        </div>
        <div class="kt-header__topbar pr-0">
          <button type="button" class="btn btn-primary btn-sm" @click="restart()">
            <i class="flaticon2-reload"></i> Restart build
          </button>
          <button
            type="button"
            class="kt-demo-icon mb-0"
            data-toggle="modal"
            data-target="#kt_modal_4"
            @click="runConfig()"
          >
            <i class="flaticon2-settings"></i>
          </button>
        </div>
      </div>
      <div class="kt-portlet__body">
        <v-card>
          <v-card-title>
            <!-- title -->
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>
            <v-spacer></v-spacer>

            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              label="Search"
              single-line
              hide-details
            ></v-text-field>
          </v-card-title>
          <v-data-table :headers="headers" :items="details" :search="search">
            <template v-slot:item.id="{ item }">
              <router-link
                :to="'/repos/' + orgName + '/' + repoName + '/' + $route.query.branch + '/' + item.id"
              >{{details.length - details.map(function(x) {return x.id; }).indexOf(item.id)}}</router-link>
            </template>

            <template v-slot:item.committer="{ item }">
              <div class="kt-user-card-v2">
                <div class="kt-user-card-v2__pic">
                  <img
                    :src="committerSrc(item.committer)"
                    class="m-img-rounded kt-marginless"
                    alt="photo"
                  />
                </div>
                <div class="kt-user-card-v2__details">
                  <a
                    :href="committerUrl(item.committer)"
                    class="kt-user-card-v2__email kt-link"
                    target="_blank"
                  >{{ item.committer }}</a>
                </div>
              </div>
            </template>

            <template v-slot:item.commit="{ item }">
              <a
                :href="repoCommit(item.commit)"
                class="kt-user-card-v2__email kt-link"
                target="_blank"
              >{{ commit(item.commit) }}</a>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip :color="getStatus(item.status)" dark>{{ item.status }}</v-chip>
            </template>

            <template v-slot:item.timestamp="{ item }">
              <span>{{ time2TimeAgo(item.timestamp) }}</span>
            </template>
          </v-data-table>
        </v-card>
      </div>
    </div>
    <!--begin::Modal-->
    <div
      class="modal fade"
      id="kt_modal_4"
      tabindex="-1"
      role="dialog"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
      v-if="newKeyModel"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Environment Variables</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!--begin::Form-->
            <form class="kt-form kt-form--label-right">
              <div class="kt-portlet__body">
                <div class="form-group" v-if="keys">
                  <div class="row" v-for="(value, key, index) in keys" :key="index">
                    <div class="col align-self-center text-right">{{ index + 1}}.</div>
                    <div class="col-md-5">
                      <input class="form-control" type="text" :value="key" disabled />
                    </div>
                    <div class="col-md-5">
                      <input class="form-control" type="password" :value="value" disabled />
                    </div>
                    <div class="col align-self-center">
                      <i class="flaticon2-delete kt-font-error" @click="deleteKey(key, value)"></i>
                    </div>
                  </div>

                  <div class="row" v-if="fireInput">
                    <div class="offset-md-1 col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Key"
                        v-model="newKey"
                        required
                      />
                    </div>
                    <div class="col-md-5">
                      <input
                        class="form-control"
                        type="text"
                        placeholder="Value"
                        v-model="newValue"
                        required
                      />
                    </div>
                  </div>

                  <div class="row">
                    <div class="offset-md-1 px-2">
                      <span class="kt-link" @click="fireInput = true">
                        <i class="flaticon2-plus"></i>
                        Add new key
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="kt-portlet__foot text-right" v-if="fireInput">
                <div class="kt-form__actions">
                  <div class="row">
                    <div class="col">
                      <button type="button" class="btn btn-success" @click.prevent="addKey()">Add</button>
                      <button type="reset" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>
<script>
import axios from "axios";
export default {
  name: "BranchDetails",
  props: ["orgName", "repoName"],
  data() {
    return {
      repos: null,
      search: "",
      headers: [
        { text: "#ID", value: "id" },
        { text: "Author", value: "committer" },
        { text: "Commit", value: "commit" },
        { text: "Status", value: "status" },
        { text: "Time", value: "timestamp" }
      ],
      details: [],
      newKeyModel: true,
      keys: null,
      fireInput: false,
      newKey: null,
      newValue: null
    };
  },
  methods: {
    getRepos() {
      const path =
        process.env.VUE_APP_BASE_URL +
        `repos/${this.orgName}/${this.repoName}?branch=${this.$route.query.branch}`;
      axios
        .get(path)
        .then(response => {
          this.details = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    clear() {
      this.details = [];
    },
    committerSrc(committer) {
      return "https://github.com/" + committer + ".png";
    },
    committerUrl(committer) {
      return "https://github.com/" + committer;
    },
    repoCommit(commit) {
      return (
        "https://github.com/" +
        this.orgName +
        "/" +
        this.repoName +
        "/commit/" +
        commit
      );
    },
    commit(commit) {
      return commit.substring(0, 7);
    },
    getStatus(status) {
      if (status == "error") return "kt-bg-error";
      else if (status == "failure") return "kt-bg-failure";
      else if (status == "success") return "kt-bg-success";
      else return "orange";
    },
    time2TimeAgo(ts) {
      var d = new Date();
      var nowTs = Math.floor(d.getTime() / 1000);
      var seconds = nowTs - ts;

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
    },
    restart() {
      const path = process.env.VUE_APP_BASE_URL + `run_trigger`;
      axios.post(
        path,
        {
          repo: this.orgName + "/" + this.repoName,
          branch: this.$route.query.branch
        },
        {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        }
      );
      this.getRepos();
    },
    runConfig() {
      const path =
        process.env.VUE_APP_BASE_URL +
        `run_config/${this.orgName}/${this.repoName}`;
      process.env.VUE_APP_BASE_URL + `run_config/AhmedHanafy725/test_zeroci`;
      axios
        .get(path)
        .then(response => {
          this.keys = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    addKey() {
      const path =
        process.env.VUE_APP_BASE_URL +
        `run_config/${this.orgName}/${this.repoName}`;
      axios.post(path, { key: this.newKey, value: this.newValue });
      this.runConfig();
      this.fireInput = false;
    },
    deleteKey(key, value) {
      const path =
        process.env.VUE_APP_BASE_URL +
        `run_config/${this.orgName}/${this.repoName}`;
      axios.delete(path, { data: { key: key, value: value } });
      this.runConfig();
    }
  },
  created() {
    this.getRepos();
  },
  watch: {
    "$route.params": {
      handler(newValue) {
        this.clear();
        const { name } = newValue;
        this.getRepos();
      },
      immediate: true
    }
  }
};
</script>

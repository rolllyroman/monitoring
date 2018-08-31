<div class="definewidth" role="form">
    <div class='header definewidth'>
        <h3>
            %if info.get('title',None):
                {{info['title']}}
            %end
        </h3>
    </div>
</div>
<div class="container-fluid">
<form class='form-horizontal group-border-dashed definewidth m10'>
        <div class="row">
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">代理账号:</span>
                <span class="form-control">{{info['account']}}</span> 
            </div>
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">代理Id:</span>
                <span class="form-control">{{info['aid']}}</span>
            </div>
        </div>  
        <div class="row">
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">代理名称:</span>
                <span class="form-control">{{info['name']}}</span>
            </div>
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">代理类型</span>
                <span class="form-control">{{info['aType']}}</span>
            </div>
            
        </div>
        <div class="row">
            <!-- <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">剩余钻石</span>
                <span class="form-control">{{info['roomCard']}}</span>
            </div> -->
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">注册时间:</span>
                <span class="form-control">{{info['regDate']}}</span>
            </div>
        </div>        
        <div class="row">
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">注册IP:</span>
                <span class="form-control">{{info['regIp']}}</span>
            </div>
            <div class="input-group col-lg-5 col-md-5 pull-left" style="padding:5px 0;margin-left:4.88%;">
                <span class="input-group-addon hint">账号状态:</span>
                <span class="form-control">{{info['valid']}}</span>
            </div>
        </div>


        
        <div class="row">
        <div class="panel panel-default">
            <div class="panel-body">
            <div class="panel-heading">管理员信息</div>
                    
                    <table class="table">
                    <thead>
                    <tr>
                        <th>用户ID</th>
                        <th>用户头像</th>
                        <th>用户名称</th>
                        <th>操作</th>
                    </tr>
                    </thead>
                    <tbody>
                        %for user in info['userDict']:
                            <tr>
                                <td>{{ user["user_id"] }}</td>
                                <td><img src="{{user['avatar_url']}}" width="40px" height="40px"></img></td>
                                <td>{{ user['name'] }}</td>
                                <td>
                                <button class="btn btn-danger delete" agent_id={{info['aid']}} user_id={{ user["user_id"] }}>删除</button>
                                </td>
                            </tr>
                       %end
                    </tbody>
                    
                
                  </table>
            </div>
            </div>
            </div>
            
        </div>
          <div class="modal-footer" style="text-align:center">
               <button type="button" class="btn btn-sm btn-primary" name="backid" id="backid">返回</button>
        </div>
        </div>
        

      
</form>
<script type="text/javascript">
    $('#backid').click(function(){
        window.location.href="{{info['backUrl']}}";
   });

   $(".delete").on("click", function(){
        var agent_id = $(this).attr("agent_id");
        var user_id = $(this).attr("user_id")
        $.ajax({
            type: 'POST',
            url: "/admin/agent/delete/"+agent_id ,
            data: {"user_id": user_id},
            dataType: "json",
            success: function(res, data){
                layer.msg(res.msg, {icon: 1});
                location.reload();
            },
            error: function(res, data){
                console.log(res)
            }, 
        
        });
   });
</script>
%rebase admin_frame_base